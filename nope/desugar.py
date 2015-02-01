import itertools

import zuice

from . import nodes, visit, couscous as cc, types, returns
from .name_declaration import DeclarationFinder
from .modules import LocalModule


def desugar(node, type_lookup, declarations):
    desugarrer = Desugarrer(type_lookup, declarations)
    return desugarrer.desugar(node)


class Desugarrer(zuice.Base):
    _type_lookup = zuice.dependency(types.TypeLookup)
    _declarations = zuice.dependency(DeclarationFinder)
    
    @zuice.init
    def init(self):
        self._unique_count = itertools.count()
    
        self._transforms = {
            LocalModule: self._local_module,
            
            nodes.Module: self._module,
            
            nodes.TypeDefinition: lambda node: cc.statements([]),
            nodes.FunctionDef: self._function_definition,
            nodes.Arguments: self._arguments,
            nodes.Argument: self._argument,
            
            nodes.WithStatement: self._with_statement,
            nodes.IfElse: self._if,
            nodes.WhileLoop: self._while,
            nodes.ForLoop: self._for_loop,
            nodes.BreakStatement: lambda node: cc.break_,
            nodes.ContinueStatement: lambda node: cc.continue_,
            
            nodes.ReturnStatement: self._return,
            nodes.RaiseStatement: self._raise,
            nodes.AssertStatement: self._assert,
            nodes.Assignment: self._assignment,
            nodes.ExpressionStatement: self._expression_statement,
            
            nodes.BinaryOperation: self._binary_operation,
            nodes.UnaryOperation: self._unary_operation,
            nodes.Subscript: self._subscript,
            nodes.Call: self._call,
            nodes.AttributeAccess: self._attr,
            nodes.VariableReference: self._ref,
            nodes.StringLiteral: self._str,
            nodes.IntLiteral: self._int,
            nodes.BooleanLiteral: self._bool,
            nodes.NoneLiteral: self._none,
            
            list: lambda nope_nodes: list(map(self.desugar, nope_nodes)),
        }
    
    def desugar(self, node):
        return self._transforms[type(node)](node)
        
    def _local_module(self, module):
        return LocalModule(module.path, self.desugar(module.node))
    
    def _module(self, module):
        exported_names = [
            attr.name
            for attr in self._type_of(module).attrs
        ]
        
        declared_names = set(self._declarations.declarations_in_module(module).names())
        declarations = list(map(cc.declare, sorted(declared_names)))
        
        return cc.module(
            declarations + self.desugar(module.body),
            is_executable=module.is_executable,
            exported_names=exported_names
        )
    
    def _with_statement(self, statement):
        exception_name = self._generate_unique_name("exception")
        manager_name = self._generate_unique_name("manager")
        exit_method_var_name = self._generate_unique_name("exit")
        has_exited_name = self._generate_unique_name("has_exited")
        
        manager_ref = cc.ref(manager_name)
        
        enter_value = cc.call(self._get_magic_method(manager_ref, "enter"), [])
        if statement.target is None:
            enter_statement = cc.expression_statement(enter_value)
        else:
            enter_statement = cc.assign(self.desugar(statement.target), enter_value)
        
        return cc.statements([
            cc.declare(manager_name, self.desugar(statement.value)),
            cc.declare(exit_method_var_name, self._get_magic_method(manager_ref, "exit")),
            cc.declare(has_exited_name, cc.false),
            enter_statement,
            cc.try_(
                self.desugar(statement.body),
                handlers=[cc.except_(self._builtin_ref("Exception"), cc.ref(exception_name), [
                    cc.assign(cc.ref(has_exited_name), cc.true),
                    cc.if_(
                        cc.not_(_bool(cc.call(cc.ref(exit_method_var_name), [
                            cc.call(self._builtin_ref("type"), [cc.ref(exception_name)]),
                            cc.ref(exception_name),
                            cc.none,
                        ]))),
                        [cc.raise_()],
                        [],
                    ),
                    
                ])],
                finally_body=[
                    cc.if_(
                        cc.not_(cc.ref(has_exited_name)),
                        [
                            cc.expression_statement(cc.call(
                                cc.ref(exit_method_var_name),
                                [cc.none, cc.none, cc.none]
                            )),
                        ],
                        [],
                    ),
                ],
            ),
        ])
    
    def _if(self, node):
        return cc.if_(
            self._condition(node.condition),
            self.desugar(node.true_body),
            self.desugar(node.false_body),
        )
    
    def _while(self, loop):
        condition = self._condition(loop.condition)
        return self._loop(loop, condition)
    
    
    def _for_loop(self, loop):
        iterator_name = self._generate_unique_name("iterator")
        element_name = self._generate_unique_name("element")
        sentinel = cc.internal("loop_sentinel")
        
        return cc.statements([
            cc.declare(iterator_name, self._call_builtin("iter", [self.desugar(loop.iterable)])),
            cc.declare(element_name),
            self._loop(
                loop,
                before_condition=[
                    cc.assign(cc.ref(element_name), self._call_builtin("next", [cc.ref(iterator_name), sentinel])),
                ],
                condition=cc.not_(cc.is_(cc.ref(element_name), sentinel)),
                after_condition=[
                    self._create_single_assignment(loop.target, cc.ref(element_name)),
                ],
            ),
        ])
        
        
    
    def _condition(self, condition):
        return self._builtins_bool(self.desugar(condition))
    
    
    def _builtins_bool(self, cc_condition):
        return self._call_builtin("bool", [cc_condition])
    
    
    def _loop(self, loop, condition, before_condition=[], after_condition=[]):
        body = self.desugar(loop.body)
        
        if loop.else_body:
            normal_exit_name = self._generate_unique_name("normal_exit")
            normal_exit = cc.ref(normal_exit_name)
            
            return cc.statements([
                cc.declare(normal_exit_name, cc.false),
                cc.while_(
                    cc.true,
                    [
                        cc.statements(before_condition),
                        cc.if_(self._negate(condition), [
                            cc.assign(normal_exit, cc.true),
                            cc.break_
                        ]),
                        cc.statements(after_condition),
                        cc.statements(body),
                    ]
                ),
                cc.if_(normal_exit, self.desugar(loop.else_body))
            ])
        elif before_condition:
            return cc.while_(cc.true, [
                cc.statements(before_condition),
                cc.if_(self._negate(condition), [
                    cc.break_,
                ]),
                cc.statements(after_condition),
                cc.statements(body),
            ])
        else:
            return cc.while_(condition, after_condition + body)
    
    def _function_definition(self, node):
        declared_names = set(self._declarations.declarations_in_function(node).names())
        arg_names = [arg.name for arg in node.args.args]
        declared_names.difference_update(arg_names)
        declarations = list(map(cc.declare, sorted(declared_names)))
        
        body = self.desugar(node.body)
        if not returns.has_unconditional_return(node.body):
            body += [cc.ret(cc.none)]
            
        return cc.func(node.name, self.desugar(node.args), declarations + body)
    
    def _arguments(self, node):
        return self.desugar(node.args)
        
    def _argument(self, node):
        return cc.arg(node.name)
    
    def _return(self, node):
        return cc.ret(self.desugar(node.value))
    
    def _raise(self, node):
        return cc.raise_(self.desugar(node.value))
        
    def _assert(self, node):
        if node.message is None:
            message = cc.str_literal("")
        else:
            message = self.transform(statement.message)
        
        exception_value = self._call_builtin("AssertionError", [message])
        
        return cc.if_(
            cc.not_(self.desugar(node.condition)),
            [cc.raise_(exception_value)],
        )
    
    def _assignment(self, node):
        value = self.desugar(node.value)
        if len(node.targets) == 1 and isinstance(node.targets[0], nodes.VariableReference):
            target, = node.targets
            return self._create_single_assignment(target, value)
        else:
            tmp_name = self._generate_unique_name("tmp")
            assignments = [
                self._create_single_assignment(target, cc.ref(tmp_name))
                for target in node.targets
            ]
            return cc.statements([cc.declare(tmp_name, value)] + assignments)
    
    def _create_single_assignment(self, target, value):
        if isinstance(target, nodes.VariableReference):
            return cc.assign(self.desugar(target), value)
        if isinstance(target, nodes.Subscript):
            call = self._call_magic_method(
                self.desugar(target.value),
                "setitem",
                self.desugar(target.slice),
                value,
            )
            return cc.expression_statement(call)
        elif isinstance(target, nodes.TupleLiteral):
            return cc.statements([
                self._create_single_assignment(target_element, cc.subscript(value, cc.int_literal(index)))
                for index, target_element in enumerate(target.elements)
            ])
        #~ # TODO: test this! Is using setattr necessary?
        #~ elif isinstance(target, nodes.AttributeAccess):
            #~ return js.assign_statement(
                #~ js.property_access(self.transform(target.value), target.attr),
                #~ value
            #~ )
        else:
            raise Exception("Unhandled case: {}".format(type(target)))
    
    def _expression_statement(self, node):
        return cc.expression_statement(self.desugar(node.value))
    
    def _binary_operation(self, node):
        left = self.desugar(node.left)
        right = self.desugar(node.right)
        if node.operator == "is":
            return cc.is_(left, right)
        elif node.operator == "is_not":
            return cc.is_not(left, right)
        elif node.operator == "bool_and":
            return cc.and_(left, right)
        elif node.operator == "bool_or":
            return cc.or_(left, right)
        else:
            return self._call_magic_method(left, node.operator, right)
    
    def _unary_operation(self, node):
        if node.operator == "bool_not":
            return cc.not_(self._condition(node.operand))
        else:
            return self._call_magic_method(self.desugar(node.operand), node.operator)
    
    def _subscript(self, node):
        return self._call_magic_method(self.desugar(node.value), "getitem", self.desugar(node.slice))
    
    def _call_magic_method(self, obj, name, *args):
        return cc.call(cc.attr(obj, "__{}__".format(name)), list(args))
    
    def _call(self, node):
        # TODO: proper support for __call__
        # at the moment, we only support meta-types that are directly callable e.g. str()
        # a better solution might be have such values have a $call attribute (or similar)
        # to avoid clashing with actual __call__ attributes
        args = []
        
        call_func_type = self._type_of(node.func)
        call_ref = node.func
        while not types.is_func_type(call_func_type) and not types.is_generic_func(call_func_type):
            call_func_type = call_func_type.attrs.type_of("__call__")
            call_ref = nodes.attr(call_ref, "__call__")
        
        for index, formal_arg in enumerate(call_func_type.args):
            if index < len(node.args):
                actual_arg_node = node.args[index]
            elif formal_arg.name in node.kwargs:
                actual_arg_node = node.kwargs[formal_arg.name]
            else:
                actual_arg_node = nodes.none()
                
            args.append(self.desugar(actual_arg_node))
            
        return cc.call(self.desugar(call_ref), args)
    
    def _attr(self, node):
        return cc.attr(self.desugar(node.value), node.attr)
    
    def _ref(self, node):
        return cc.ref(node.name)
    
    def _str(self, node):
        return cc.str_literal(node.value)
    
    def _int(self, node):
        return cc.int_literal(node.value)
    
    def _bool(self, node):
        return cc.bool_literal(node.value)
    
    def _none(self, node):
        return cc.none

    def _negate(self, node):
        if isinstance(node, cc.UnaryOperation) and node.operator == "not":
            return node.operand
        else:
            return cc.not_(node)

    
    def _type_of(self, node):
        return self._type_lookup.type_of(node)
    
    def _get_magic_method(self, receiver, name):
        # TODO: get magic method through the same mechanism as self._call
        return cc.attr(receiver, "__{}__".format(name))
    
    def _call_builtin(self, name, args):
        return cc.call(self._builtin_ref(name), args)
    
    def _builtin_ref(self, name):
        return cc.builtin(name)

    def _generate_unique_name(self, name):
        return "${}{}".format(name, next(self._unique_count))

def _bool(value):
    return cc.call(cc.builtin("bool"), [value])
