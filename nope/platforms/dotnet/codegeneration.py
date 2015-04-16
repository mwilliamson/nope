import os
import subprocess
import functools
import hashlib

import zuice

from ... import files
from ...walk import walk_tree
from ...injection import CouscousTree
from . import cs
from ... import couscous as cc
from ...modules import Module, LocalModule, BuiltinModule
from ...module_resolution import ModuleResolver
from ...iterables import find


class CodeGenerator(zuice.Base):
    _source_tree = zuice.dependency(CouscousTree)
    _module_resolver_factory = zuice.dependency(zuice.factory(ModuleResolver))
    
    def generate_files(self, source_path, destination_root):
        cs_filenames = self._generate_cs_files(source_path, destination_root)
        stdlib_filenames = self._generate_stdlib_files(destination_root)
        
        def handle_dir(path, relative_path):
            files.mkdir_p(os.path.join(destination_root, relative_path))
        
        def handle_file(path, relative_path):
            module = self._source_tree.module(path)
            if module.node.is_executable:
                dest_exe_filename = files.replace_extension(
                    os.path.join(destination_root, relative_path),
                    "exe"
                )

                subprocess.check_call([
                    "mcs", "-nowarn:0162,0168,0219,0414,0649",
                    "-out:{}".format(dest_exe_filename)
                ] + cs_filenames + stdlib_filenames + list(_runtime_paths()))

        walk_tree(source_path, handle_dir, handle_file)

    def _generate_stdlib_files(self, destination_root):
        stdlib_path = os.path.join(os.path.dirname(__file__), "../../../stdlib")
        destination_stdlib_path = os.path.join(destination_root, "__stdlib")
        
        def handle_dir(path, relative_path):
            files.mkdir_p(os.path.join(destination_stdlib_path, relative_path))
        
        cs_filenames = []
        
        def handle_file(path, relative_path):
            dest_cs_filename = files.replace_extension(
                os.path.join(destination_stdlib_path, relative_path),
                "cs"
            )
            self._generate_cs_file(path, dest_cs_filename)
            cs_filenames.append(dest_cs_filename)
        
        walk_tree(stdlib_path, handle_dir, handle_file)
        return cs_filenames
    
    def _generate_cs_files(self, source_path, destination_root):
        def handle_dir(path, relative_path):
            files.mkdir_p(os.path.join(destination_root, relative_path))
        
        cs_filenames = []
        
        def handle_file(path, relative_path):
            dest_cs_filename = files.replace_extension(
                os.path.join(destination_root, relative_path),
                "cs"
            )
            self._generate_cs_file(path, dest_cs_filename)
            cs_filenames.append(dest_cs_filename)
            
        walk_tree(source_path, handle_dir, handle_file)
        return cs_filenames
    
    def _generate_cs_file(self, path, dest_path):
        module = self._source_tree.module(path)
        transformer = Transformer(
            module_resolver=self._module_resolver_factory({Module: module}),
            prelude=self._prelude,
            path_hash=self._sha1_hash,
        )
        cs_module = transformer.transform(module)
        
        with open(dest_path, "w") as dest_cs_file:
            cs.dump(cs_module, dest_cs_file)
    
    def _sha1_hash(self, value):
        return hashlib.sha1(value.encode("utf8")).hexdigest()
    
    _prelude = """
    private static System.Func<dynamic, dynamic> abs = __x_1 => __x_1.__abs__();
    private static System.Func<dynamic, dynamic, dynamic> divmod = (__x_1, __y_1) => __x_1.__divmod__(__y_1);
    private static System.Func<dynamic, dynamic, dynamic> range = (__x_1, __y_1) => __Nope.Builtins.range(__x_1, __y_1);
    private static System.Action<dynamic> print = (System.Action<dynamic>)(obj => System.Console.WriteLine(obj.__str__().__Value));
    private static dynamic Exception = __Nope.Builtins.Exception;
    private static dynamic AssertionError = __Nope.Builtins.AssertionError;
    private static dynamic StopIteration = __Nope.Builtins.StopIteration;
    private static dynamic str = __Nope.Builtins.str;
"""

def _runtime_paths():
    path = os.path.join(os.path.dirname(__file__), "runtime")
    for root, dirnames, filenames in os.walk(path):
        for filename in filenames:
            yield os.path.join(root, filename)


class Transformer(object):
    def __init__(self, module_resolver, prelude, path_hash):
        self._module_resolver = module_resolver
        self._prelude = prelude
        self._path_hash = path_hash
        self._transformers = {
            LocalModule: self._transform_module,
            
            cc.ModuleReference: self._transform_module_reference,
            
            cc.Statements: self._transform_statements,
            
            cc.ClassDefinition: self._transform_class_definition,
            cc.FunctionDefinition: self._transform_function_definition,
            
            cc.IfStatement: self._transform_if_statement,
            cc.WhileLoop: self._transform_while_loop,
            cc.BreakStatement: lambda node: cs.break_,
            cc.ContinueStatement: lambda node: cs.continue_,
            
            cc.TryStatement: self._transform_try_statement,
            cc.RaiseStatement: self._transform_raise_statement,
            
            cc.ExpressionStatement: self._transform_expression_statement,
            cc.VariableDeclaration: self._transform_variable_declaration,
            cc.ReturnStatement: self._transform_return_statement,
            
            cc.FormalArgument: self._transform_argument,
            
            cc.Assignment: self._transform_assignment,
            cc.FunctionExpression: self._transform_function_expression,
            cc.ListLiteral: self._transform_list_literal,
            cc.TupleLiteral: self._transform_tuple_literal,
            cc.BinaryOperation: self._transform_operation,
            cc.UnaryOperation: self._transform_operation,
            cc.TernaryConditional: self._transform_ternary_conditional,
            cc.Call: self._transform_call,
            cc.AttributeAccess: self._transform_attribute_access,
            cc.BuiltinReference: _transform_builtin_reference,
            cc.InternalReference: _transform_internal_reference,
            cc.VariableReference: _transform_variable_reference,
            cc.StrLiteral: _transform_string_literal,
            cc.IntLiteral: _transform_int_literal,
            cc.BooleanLiteral: _transform_bool_literal,
            cc.NoneLiteral: _transform_none_literal,
        }
        self._aux = []
    
    
    def transform(self, node):
        return self._transformers[type(node)](node)
    
    
    def aux(self):
        return cs.statements(self._aux)


    def _transform_all(self, nodes):
        return list(map(self.transform, nodes))


    def _transform_or_none(self, node):
        if node is None:
            return None
        else:
            return self.transform(node)


    def _transform_module(self, module):
        child_transformer = Transformer(
            module_resolver=self._module_resolver,
            prelude=self._prelude,
            path_hash=self._path_hash)
        body = child_transformer._transform_all(module.node.body)
        
        if module.node.is_executable:
            main = cs.method("Main", [], body, static=True, returns=cs.void)
            class_name = "Program"
        else:
            module_name = "__module"
            module_ref = cs.ref(module_name)
            return_module = [
                cs.declare(module_name, cs.new(cs.ref("System.Dynamic.ExpandoObject"), [])),
                cs.statements([
                    cs.assign_statement(cs.property_access(module_ref, exported_name), cs.ref(exported_name))
                    for exported_name in module.node.exported_names
                ]),
                cs.ret(module_ref),
            ]
            main = cs.method("Init", [], body + return_module, static=True)
            class_name = self._module_to_class_name(module)
        
        return cs.class_(class_name, [
            cs.raw(self._prelude),
            main,
            child_transformer.aux(),
        ])
    

    def _transform_module_reference(self, reference):
        module = self._module_resolver.resolve_import_path(reference.names)
        init = cs.property_access(cs.ref(self._module_to_class_name(module)), "Init")
        return cs.call(_internal_ref("Import"), [init])
    
    
    def _module_to_class_name(self, module):
        return "__".join(["Module", self._path_hash(os.path.normpath(module.path))])


    def _transform_statements(self, node):
        return cs.statements(self._transform_all(node.body))


    def _transform_class_definition(self, node):
        aux_name = "__" + node.name
        
        methods = [
            (method.name, self._transform_method(method))
            for method in node.methods
        ]
        method_names = [method.name for method in node.methods]
        
        if "__init__" in method_names:
            init_method = find(lambda method: method.name == "__init__", node.methods)
            init_arg_names = ["__" + arg.name for arg in init_method.args[1:]]
            
            # TODO: this doesn't account for if statements and whatnot.
            # Should probably just be using the class type that type inference generated.
            assigned_names = [
                assignment.target.attr
                for assignment in _flatten_statements(init_method.body)
                if (
                    isinstance(assignment, cc.Assignment) and
                    isinstance(assignment.target, cc.AttributeAccess) and
                    isinstance(assignment.target.obj, cc.VariableReference) and
                    assignment.target.obj.name == init_method.args[0].name
                )
            ]
        else:
            init_method = None
            init_arg_names = []
            assigned_names = []
        
        member_names = method_names + assigned_names
        
        aux_class = cs.class_(aux_name, list(map(cs.field, member_names)))
        self._aux.append(aux_class)
        
        new_obj = cs.new(cs.ref(aux_name), [], methods)
        
        call_func_body = [
            cs.declare("__self", cs.null),
            cs.expression_statement(cs.assign(cs.ref("__self"), new_obj)),
        ]
        if init_method is not None:
            init_ref = cs.property_access(cs.ref("__self"), "__init__")
            call_init = cs.call(init_ref, list(map(cs.ref, init_arg_names)))
            call_func_body.append(cs.expression_statement(call_init))
        
        call_func_body.append(cs.ret(cs.ref("__self")))
        call_func = cs.lambda_(list(map(cs.arg, init_arg_names)), call_func_body)
        
        class_obj = cs.obj([
            ("__call__", cs.cast(self._func_type(len(init_arg_names)), call_func)),
        ])
        return cs.expression_statement(cs.assign(node.name, class_obj))


    def _transform_method(self, method):
        args = method.args[1:]
        func_type = self._func_type(len(args))
        args = [cs.arg(arg.name) for arg in args]
        body = [cs.declare(method.args[0].name, cs.ref("__self"))] + self._transform_all(method.body)
        lambda_expression = cs.lambda_(args, body)
        return cs.cast(func_type, lambda_expression)


    def _transform_function_definition(self, function):
        func_type = self._func_type(len(function.args))
        args = self._transform_all(function.args)
        body = self._transform_all(function.body)
        lambda_expression = cs.lambda_(args, body)
        assignment = cs.assign(cs.ref(function.name), cs.cast(func_type, lambda_expression))
        return cs.expression_statement(assignment)


    def _func_type(self, length):
        return cs.type_apply(cs.ref("System.Func"), [cs.dynamic] * (length + 1))


    def _transform_if_statement(self, statement):
        return cs.if_(
            self._transform_condition(statement.condition),
            self._transform_all(statement.true_body),
            self._transform_all(statement.false_body)
        )


    def _transform_while_loop(self, statement):
        return cs.while_(
            self._transform_condition(statement.condition),
            self._transform_all(statement.body),
        )

    def _transform_condition(self, condition):
        return cs.property_access(self.transform(condition), "__Value")


    def _transform_try_statement(self, statement):
        if statement.handlers:
            catch = [self._transform_except_handlers(statement.handlers)]
        else:
            catch = []
        
        return cs.try_(
            self._transform_all(statement.body),
            catch,
            finally_body=self._transform_all(statement.finally_body),
        )


    def _transform_except_handlers(self, handlers):
        catch_body = [cs.throw()]
        
        dotnet_exception_name = "__exception"
        dotnet_exception = cs.ref(dotnet_exception_name)
        
        nope_exception = cs.property_access(dotnet_exception, "__Value")
        
        for handler in reversed(handlers):
            handler_body = self._transform_all(handler.body)
            
            if handler.type is None:
                catch_body = handler_body
            else:
                if handler.target is None:
                    before_body = []
                else:
                    before_body = [cs.expression_statement(cs.assign(cs.ref(handler.target.name), nope_exception))]
                
                catch_body = [
                    cs.if_(
                        cs.property_access(cs.call(_builtin_ref("isinstance"), [nope_exception, self.transform(handler.type)]), "__Value"),
                        before_body + handler_body,
                        catch_body,
                    )
                ]
        
        return cs.catch(_internal_ref("__NopeException"), dotnet_exception_name, catch_body)


    def _transform_raise_statement(self, statement):
        if statement.value is None:
            return cs.throw()
        else:
            return cs.throw(cs.call(_internal_ref("CreateException"), [self.transform(statement.value)]))


    def _transform_expression_statement(self, statement):
        return cs.expression_statement(self.transform(statement.value))


    def _transform_variable_declaration(self, declaration):
        if declaration.value is None:
            value = cs.null
        else:
            value = self.transform(declaration.value)
        return cs.declare(declaration.name, value)

    def _transform_argument(self, argument):
        return cs.arg(argument.name)

    def _transform_function_expression(self, function):
        args = self._transform_all(function.args)
        body = self._transform_all(function.body)
        return cs.lambda_(args, body)

    def _transform_operation(self, operation):
        if operation.operator in ["is", "is_not"]:
            return self._transform_is(operation)
        elif operation.operator == "not":
            return self._transform_not(operation)
        else:
            raise Exception("Unhandled operator: {}".format(operation.operator))


    def _transform_ternary_conditional(self, conditional):
        return cs.ternary_conditional(
            self._transform_condition(conditional.condition),
            self.transform(conditional.true_value),
            self.transform(conditional.false_value),
        )


    def _transform_is(self, operation):
        return cs.call(cs.ref("__Nope.Internals.op_{}".format(operation.operator)), [
            self.transform(operation.left),
            self.transform(operation.right),
        ])


    def _transform_not(self, operation):
        return cs.call(cs.property_access(self.transform(operation.operand), "__Negate"), [])


    def _transform_return_statement(self, statement):
        return cs.ret(self.transform(statement.value))


    def _transform_assignment(self, assignment):
        return cs.expression_statement(cs.assign(self.transform(assignment.target), self.transform(assignment.value)))


    def _transform_list_literal(self, literal):
        return cs.call(cs.ref("__NopeList.Values"), self._transform_all(literal.elements))


    def _transform_tuple_literal(self, literal):
        return cs.call(cs.ref("__NopeTuple.Values"), self._transform_all(literal.elements))


    def _transform_call(self, call):
        return cs.call(self.transform(call.func), self._transform_all(call.args))


    def _transform_attribute_access(self, node):
        return cs.property_access(self.transform(node.obj), node.attr)


def _transform_builtin_reference(reference):
    return _builtin_ref(reference.name)


def _builtin_ref(name):
    return cs.ref("__Nope.Builtins.@{}".format(name))


def _transform_internal_reference(reference):
    return _internal_ref(reference.name)


def _internal_ref(name):
    return cs.ref("__Nope.Internals.@{}".format(name))


def _transform_variable_reference(reference):
    return cs.ref(reference.name)


def _transform_string_literal(literal):
    return cs.call(cs.ref("__NopeString.Value"), [cs.string_literal(literal.value)])


def _transform_int_literal(literal):
    return cs.call(cs.ref("__NopeInteger.Value"), [cs.integer_literal(literal.value)])


def _transform_bool_literal(literal):
    return cs.ref("__NopeBoolean.{}".format("True" if literal.value else "False"))


def _transform_none_literal(literal):
    return cs.ref("__NopeNone.Value")


def _flatten_statements(statements):
    for statement in statements:
        if isinstance(statement, cc.Statements):
            for child in statement.body:
                yield child
        else:
            yield statement
