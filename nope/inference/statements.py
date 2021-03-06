import os
import functools

from .. import nodes, types, returns, errors, builtins
from . import ephemeral
from .assignment import Assignment
from .classes import ClassDefinitionTypeChecker


class StatementTypeChecker(object):
    def __init__(self, declaration_finder, expression_type_inferer, module_resolver, module_types, module):
        self._expression_type_inferer = expression_type_inferer
        self._module_resolver = module_resolver
        self._module_types = module_types
        self._module = module
        
        class_definition_type_checker = ClassDefinitionTypeChecker(
            self,
            declaration_finder,
            expression_type_inferer
        )
        
        self._checkers = {
            nodes.ExpressionStatement: self._check_expression_statement,
            nodes.ReturnStatement: self._check_return,
            nodes.Assignment: self._check_assignment,
            nodes.IfElse: self._check_if_else,
            nodes.WhileLoop: self._check_while_loop,
            nodes.ForLoop: self._check_for_loop,
            nodes.BreakStatement: self._check_break,
            nodes.ContinueStatement: self._check_continue,
            nodes.TryStatement: self._check_try,
            nodes.RaiseStatement: self._check_raise,
            nodes.AssertStatement: self._check_assert,
            nodes.WithStatement: self._check_with,
            nodes.FunctionDef: self._check_function_def,
            nodes.ClassDefinition: class_definition_type_checker.check_class_definition,
            nodes.TypeDefinition: self._check_type_definition,
            nodes.StructuralTypeDefinition: self._check_structural_type_definition,
            nodes.Import: self._check_import,
            nodes.ImportFrom: self._check_import_from,
            nodes.Statements: self._check_statements,
            list: self._check_list,
        }
    
    def update_context(self, statement, context, immediate=False):
        self._checkers[type(statement)](statement, context)
        if immediate:
            context.update_deferred(statement)

    def _find_submodule(self, name):
        try:
            return self._module_resolver.resolve_import_path([".", name])
        except errors.ModuleNotFoundError:
            return None
    
    def infer_function_def(self, node, context):
        signature = self._read_signature(node, node.type, context)
        self._check_signature(signature, node)
        return signature
    
    def _read_signature(self, node, signature, context):
        if signature is None:
            if len(node.args.args) == 0:
                return types.func([], types.none_type)
            else:
                raise errors.ArgumentsError(node, "signature is missing from function definition")
        else:
            return self._infer_type_value(signature, context)
    
    def _check_signature(self, signature, node):
        if len(node.args.args) != len(signature.args):
            raise errors.ArgumentsError(signature, "args length mismatch: def has {0}, signature has {1}".format(
                len(node.args.args), len(signature.args)))
        
        for def_arg, signature_arg in zip(node.args.args, signature.args):
            if signature_arg.name is not None and def_arg.name != signature_arg.name:
                raise errors.ArgumentsError(
                    signature_arg,
                    "argument '{}' has name '{}' in signature".format(def_arg.name, signature_arg.name)
                )
            if signature_arg.optional and not def_arg.optional:
                raise errors.ArgumentsError(
                    signature_arg,
                    "optional argument '{}' must have default value".format(def_arg.name)
                )

    def _check_function_def(self, node, context):
        func_type = self.infer_function_def(node, context)
        context.update_type(node, func_type)
        context.add_deferred(
            node,
            functools.partial(self._check_function_def_body, node, func_type, context)
        )
    
    def _check_function_def_body(self, node, func_type, context):
        return_type = func_type.return_type
        
        body_context = context.enter_func(return_type)
        
        if types.is_generic_func(func_type):
            for formal_type_param_node, formal_type_param in zip(node.type.type_params, func_type.formal_type_params):
                body_context.update_type(formal_type_param_node, types.meta_type(formal_type_param))
        
        body_arg_types = [
            self._infer_function_def_arg_type(arg, formal_arg, body_context)
            for arg, formal_arg in zip(node.args.args, func_type.args)
        ]
            
        for arg, body_arg_type in zip(node.args.args, body_arg_types):
            body_context.update_type(arg, body_arg_type)
        
        self.update_context(node.body, body_context)
        
        if return_type != types.none_type and not returns.has_unconditional_return(node.body):
            raise errors.MissingReturnError(node, return_type)
        
    
    def _infer_function_def_arg_type(self, arg, formal_arg, context):
        if arg.optional:
            return types.union(formal_arg.type, types.none_type)
        else:
            return formal_arg.type
    
    
    def _check_type_definition(self, node, context):
        context.update_type(node, self._infer(node.value, context))
    
    
    def _check_structural_type_definition(self, node, context):
        structural_type = types.structural_type(node.name, [
            types.attr(name, self._infer_type_value(type_expression, context))
            for name, type_expression in node.attrs
        ])
        context.update_type(node, types.meta_type(structural_type))
    

    def _check_expression_statement(self, node, context):
        self._infer(node.value, context)


    def _check_return(self, node, context):
        expected = context.return_type
        actual = self._infer(node.value, context)
        if not types.is_sub_type(expected, actual):
            raise errors.UnexpectedValueTypeError(node, expected, actual)


    def _check_assignment(self, node, context):
        if node.type is not None:
            required_type = self._infer_type_value(node.type, context)
            hint = None
        elif len(node.targets) == 1 and isinstance(node.targets[0], nodes.VariableReference):
            required_type = None
            hint = context.lookup(node.targets[0], allow_unbound=True)
        else:
            required_type = None
            hint = None
        
        value_type = self._infer(node.value, context, hint=hint, required_type=required_type)
        
        for target in node.targets:
            self._assign(node, target, value_type, context)
    
    def _assign(self, node, target, value_type, context):
        assignment = Assignment(self._expression_type_inferer, on_ref=self._check_ref)
        assignment.assign(node, target, value_type, context)
    
    def _check_ref(self, target, value_type, context):
        if context.is_module_scope and self._is_package():
            self._check_for_package_value_and_module_name_clashes(target, value_type)

    def _is_package(self):
        return self._module.path and os.path.basename(self._module.path) == "__init__.py"

    def _check_for_package_value_and_module_name_clashes(self, target, value_type):
        submodule = self._find_submodule(target.name)
        if submodule is not None:
            if value_type is not submodule:
                raise errors.ImportedValueRedeclaration(target, target.name)
    
    
    def _check_if_else(self, node, context):
        self._infer(node.condition, context)
        self._check_list(node.true_body, context)
        self._check_list(node.false_body, context)

    def _check_while_loop(self, node, context):
        self._infer(node.condition, context)
        self._check_list(node.body, context)
        self._check_list(node.else_body, context)
    
    def _check_for_loop(self, node, context):
        element_type = self._infer_for_loop_element_type(node, context)
        self._assign(node, node.target, element_type, context)
        self._check_list(node.body, context)
        self._check_list(node.else_body, context)
    
    
    def _infer_for_loop_element_type(self, node, context):
        return self._expression_type_inferer.infer_iterable_element_type(node.iterable, context)
    
    
    def _check_break(self, node, context):
        pass
    
    
    def _check_continue(self, node, context):
        pass
    
    
    def _check_try(self, node, context):
        self._check_list(node.body, context)
        
        for handler in node.handlers:
            exception_type = self._infer_handler_exception_type(handler, context)
            if handler.target is not None:
                self._assign(handler, handler.target, exception_type, context)
            self._check_list(handler.body, context)
        
        self._check_list(node.finally_body, context)

        
    def _infer_handler_exception_type(self, handler, context):
        if handler.type:
            handled_type = self._infer_type_value(handler.type, context)
            if not types.is_sub_type(types.exception_type, handled_type):
                raise errors.UnexpectedValueTypeError(handler.type,
                    expected="exception type",
                    actual=self._infer(handler.type, context),
                )
            return handled_type
    
    
    def _check_raise(self, node, context):
        exception_type = self._infer(node.value, context)
        if not types.is_sub_type(types.exception_type, exception_type):
            raise errors.UnexpectedValueTypeError(
                node.value,
                expected=types.exception_type,
                actual=exception_type,
            )
    
    
    def _check_assert(self, node, context):
        self._infer(node.condition, context)
        if node.message is not None:
            self._infer(node.message, context)
    
    def _check_with(self, node, context):
        enter_return_type = self._infer_magic_method_call(node.value, "enter", node.value, [], context)
        
        exit_arg_types = [
            types.union(types.exception_meta_type, types.none_type),
            types.union(types.exception_type, types.none_type),
            types.union(types.traceback_type, types.none_type)
        ]
        
        exit_type = self._infer_magic_method_call(
            node.value,
            "exit",
            node.value,
            [
                ephemeral.formal_arg_constraint(type_)
                for type_ in exit_arg_types
            ],
            context,
        )
        
        if node.target is not None:
            self._assign(node.target, node.target, enter_return_type, context)
        self._check_list(node.body, context)

    def _check_import(self, node, context):
        for alias in node.names:
            self._check_import_alias(node, alias, context)
        
    def _check_import_alias(self, node, alias, context):
        if alias.asname is None:
            parts = alias.original_name_parts
            
            for index, part in enumerate(parts):
                this_module = self._find_module(node, parts[:index + 1])
                
                if index == 0:
                    binding = context.lookup(alias, allow_unbound=True)
                    if binding is None:
                        context.update_type(alias, this_module)
                    elif not types.is_module(binding) or binding.name != this_module.name:
                        raise errors.UnexpectedTargetTypeError(node,
                            target_type=binding, value_type=this_module)
                    else:
                        this_module = binding
                else:
                    last_module.attrs.add(part, this_module)
                    
                last_module = this_module
            
        else:
            module = self._find_module(node, alias.original_name_parts)
            context.update_type(alias, module)


    def _check_import_from(self, node, context):
        for alias in node.names:
            module_type = self._find_module(node, node.module, alias.original_name)
            context.update_type(alias, module_type)
    
    
    def _check_statements(self, node, context):
        self.update_context(node.body, context)
    
    
    def _find_module(self, node, names, value_name=None):
        try:
            resolved_import = self._module_resolver.resolve_import_value(names, value_name)
        except errors.TypeCheckError as error:
            error.node = node
            raise error
        
        if hasattr(resolved_import.module, "type"):
            module_type = resolved_import.module.type
        else:
            module_type = self._module_types.type_of_module(resolved_import.module)
        
        module_type = module_type.copy()
        
        if resolved_import.attr_name is None:
            return module_type
        else:
            return module_type.attrs.type_of(resolved_import.attr_name)
        
    def _infer(self, node, context, hint=None, required_type=None):
        return self._expression_type_inferer.infer(node, context, hint=hint, required_type=required_type)
    
    def _check_list(self, statements, context):
        for statement in statements:
            self.update_context(statement, context)
    
    def _infer_magic_method_call(self, *args, **kwargs):
        return self._expression_type_inferer.infer_magic_method_call(*args, **kwargs)
    
    def _infer_type_value(self, *args, **kwargs):
        return self._expression_type_inferer.infer_type_value(*args, **kwargs)
    
    def _type_of_module(self, path):
        if self._module_types.is_module_path(path):
            return self._module_types.type_of_module(path)
        else:
            return None
