import os

from .. import nodes, types, util, returns, errors, name_declaration
from . import ephemeral
from .assignment import Assignment


class StatementTypeChecker(object):
    def __init__(self, declaration_finder, expression_type_inferer, module_resolver, module_types, module):
        self._declaration_finder = declaration_finder
        self._expression_type_inferer = expression_type_inferer
        self._module_resolver = module_resolver
        self._module_types = module_types
        self._module = module
        
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
            nodes.ClassDefinition: self._check_class_definition,
            nodes.Import: self._check_import,
            nodes.ImportFrom: self._check_import_from,
            list: self._check_list,
        }

    def update_context(self, statement, context):
        self._checkers[type(statement)](statement, context)

    def _find_submodule(self, name):
        try:
            return self._module_resolver.resolve_import(self._module, [".", name])
        except errors.ModuleNotFoundError:
            return None
    
    def _infer_function_def(self, node, context):
        signature = nodes.explicit_type_of(node)
        args, return_type = self._read_signature(signature, context)
        self._check_signature(signature, node)
        return types.func(args, return_type)
    
    def _read_signature(self, signature, context):
        if signature is None:
            return [], types.none_type
        else:
            args = [self._read_signature_arg(arg, context) for arg in signature.args]
            return_type = self._infer_type_value(signature.returns, context)
            return args, return_type
    
    def _read_signature_arg(self, arg, context):
        return types.func_arg(
            arg.name,
            self._infer_type_value(arg.type, context),
        )
    
    def _check_signature(self, signature, node):
        if signature is None:
            if len(node.args.args) == 0:
                signature = nodes.signature(type_params=[], args=[], returns=None)
            else:
                raise errors.ArgumentsError(node, "signature is missing from function definition")
        
        if len(node.args.args) != len(signature.args):
            raise errors.ArgumentsError(signature, "args length mismatch: def has {0}, signature has {1}".format(
                len(node.args.args), len(signature.args)))
        
        for def_arg, signature_arg in zip(node.args.args, signature.args):
            if signature_arg.name is not None and def_arg.name != signature_arg.name:
                raise errors.ArgumentsError(
                    signature_arg,
                    "argument '{}' has name '{}' in signature".format(def_arg.name, signature_arg.name)
                )

    def _check_function_def(self, node, context):
        func_type = self._infer_function_def(node, context)
        
        return_type = func_type.return_type
        
        body_context = context.enter_func(return_type)
        
        for arg, formal_arg in zip(node.args.args, func_type.args):
            body_context.update_type(arg, formal_arg.type)
            
        self.update_context(node.body, body_context)
        
        if return_type != types.none_type and not returns.has_unconditional_return(node.body):
            raise errors.MissingReturnError(node, return_type)
        
        context.update_type(node, func_type)
        
    
    def _check_class_definition(self, node, context):
        base_classes = [
            self._infer_type_value(base_class, context)
            for base_class in node.base_classes
        ]
        if any(base_class != types.object_type for base_class in base_classes):
            raise errors.UnsupportedError("base classes other than 'object' are not supported")
        
        class_type = types.scalar_type(node.name)
        meta_type = types.meta_type(class_type)
        
        class_declarations = self._declaration_finder.declarations_in_class(node)
        attr_names = class_declarations.names()
        
        body_context = context.enter_class()
        body_context.update_declaration_type(
            class_declarations.declaration("Self"),
            meta_type
        )
        
        function_definitions = []
        assignments = []
        for statement in node.body:
            if isinstance(statement, nodes.FunctionDef):
                function_definitions.append(statement)
            elif isinstance(statement, nodes.Assignment):
                for target in statement.targets:
                    if isinstance(target, nodes.VariableReference) and target.name == "__init__":
                        raise errors.InitAttributeMustBeFunctionDefinitionError(statement)
                assignments.append(statement)
            else:
                # The type of statements in a class body should have
                # been verified in an earlier stage.
                raise Exception("Unexpected statement in class body")
        
        def add_attr_to_type(attr_name, attr_type):
            is_init_method = attr_name == "__init__"
            is_func_type = types.is_func_type(attr_type)
            
            if types.is_func_type(attr_type):
                self._check_method_receiver_argument(node, class_type, attr_name, attr_type)
                method_type = self._function_type_to_method_type(attr_type)
                if is_init_method:
                    if method_type.return_type != types.none_type:
                        raise errors.InitMethodsMustReturnNoneError(node)
                else:
                    class_type.attrs.add(attr_name, method_type)
            else:
                class_type.attrs.add(attr_name, attr_type)
                meta_type.attrs.add(attr_name, attr_type)
        
        for assignment in assignments:
            self.update_context(assignment, body_context)        
            attr_type = self._infer(assignment.value, body_context)
            for target in assignment.targets:
                if isinstance(target, nodes.VariableReference):
                    add_attr_to_type(target.name, attr_type)
        
        for function_definition in function_definitions:
            func_type = self._infer_function_def(function_definition, body_context)
            add_attr_to_type(function_definition.name, func_type)
            if function_definition.name == "__init__":
                self._check_init_method(function_definition, body_context, class_type)                
                self.update_context(function_definition, body_context)
        
        for function_definition in function_definitions:
            if function_definition.name != "__init__":
                self.update_context(function_definition, body_context)
        
        if "__init__" in attr_names:
            init_declaration = class_declarations.declaration("__init__")
            init_func_type = body_context.lookup_declaration(init_declaration)
            init_method_type = self._function_type_to_method_type(init_func_type)
            constructor_type = types.func(init_method_type.args, class_type)
        else:
            constructor_type = types.func([], class_type)
        
        meta_type.attrs.add("__call__", constructor_type, read_only=True)
        context.update_type(node, meta_type)
    
    def _check_init_method(self, node, context, class_type):
        declarations_in_function = self._declaration_finder.declarations_in_function(node)
        self_arg_name = node.args.args[0].name
        self_declaration = declarations_in_function.declaration(self_arg_name)
        for statement in node.body:
            # TODO: relax this constraint
            if isinstance(statement, nodes.Assignment):
                for target in statement.targets:
                    is_self_attr_assignment = (
                        isinstance(target, nodes.AttributeAccess) and
                        context.referenced_declaration(target.value) == self_declaration
                    )
                    if is_self_attr_assignment:
                        value_type = self._infer(statement.value, context)
                        class_type.attrs.add(target.attr, value_type)
                
    
    def _function_type_to_method_type(self, func_type):
        return types.func(func_type.args[1:], func_type.return_type)
    
    def _check_method_receiver_argument(self, class_node, class_type, attr_name, func_type):
        if len(func_type.args) < 1:
            raise errors.MethodHasNoArgumentsError(class_node, attr_name)
        
        formal_receiver_type = func_type.args[0].type
        if not types.is_sub_type(formal_receiver_type, class_type):
            raise errors.UnexpectedReceiverTypeError(
                class_node,
                receiver_type=formal_receiver_type,
            )


    def _check_expression_statement(self, node, context):
        self._infer(node.value, context)


    def _check_return(self, node, context):
        expected = context.return_type
        actual = self._infer(node.value, context)
        if not types.is_sub_type(expected, actual):
            raise errors.UnexpectedValueTypeError(node, expected, actual)


    def _check_assignment(self, node, context):
        value_type = self._infer(node.value, context)
        for target in node.targets:
            self._assign(node, target, value_type, context)
    
    def _assign(self, node, target, value_type, context):
        assignment = Assignment(self._expression_type_inferer, on_ref=self._check_ref)
        assignment.assign(node, target, value_type, context)
    
    def _check_ref(self, target, value_type, context):
        if self._is_package() and context.is_module_scope:
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
                # TODO: strictly speaking, this error should have the
                # meta-types rather than the actual types
                raise errors.UnexpectedValueTypeError(handler.type,
                    expected="exception",
                    actual=handled_type,
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
        
        exit_return_type = self._infer_magic_method_call(
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
            if alias.asname is None:
                parts = alias.name_parts
                
                for index, part in enumerate(parts):
                    this_module = self._find_module(node, parts[:index + 1])
                    
                    if index == 0:
                        context.update_type(alias, this_module)
                    else:
                        # TODO: set readonly
                        last_module.attrs.add(part, this_module)
                        
                    last_module = this_module
                
            else:
                module = self._find_module(node, alias.name_parts)
                context.update_type(alias, module)


    def _check_import_from(self, node, context):
        module = self._find_module(node, node.module)
        for alias in node.names:
            module_value = module.attrs.type_of(alias.name)
            if module_value is not None:
                context.update_type(alias, module_value)
            else:
                submodule = self._find_module(node, node.module + [alias.name])
                # TODO: set readonly
                module.attrs.add(alias.value_name, submodule)
                context.update_type(alias, submodule)

    
    def _find_module(self, node, names):
        try:
            module = self._module_resolver.resolve_import(self._module, names)
        except errors.TypeCheckError as error:
            error.node = node
            raise error
        
        if hasattr(module, "type"):
            return module.type.copy()
        else:
            return self._module_types.type_of_module(module).copy()

    def _possible_module_paths(self, names):
        import_path = os.path.normpath(os.path.join(os.path.dirname(self._module.path), *names))
        
        return (
            os.path.join(import_path, "__init__.py"),
            import_path + ".py"
        )
        
    def _infer(self, node, context):
        return self._expression_type_inferer.infer(node, context)
    
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
