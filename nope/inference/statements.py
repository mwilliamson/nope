import os

from .. import nodes, types, util, returns, errors
from . import ephemeral


class StatementTypeChecker(object):
    def __init__(self, expression_type_inferer, source_tree, module_path, is_executable):
        self._expression_type_inferer = expression_type_inferer
        self._source_tree = source_tree
        self._module_path = module_path
        self._is_executable = is_executable
        
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
            nodes.Import: self._check_import,
            nodes.ImportFrom: self._check_import_from,
            list: self._check_list,
        }

    def update_context(self, statement, context):
        self._checkers[type(statement)](statement, context)

    def _find_submodule(self, name):
        for path in self._possible_module_paths([".", name]):
            if path in self._source_tree:
                return self._source_tree.import_module(path)
        
        return None
    
    def _infer_function_def(self, node, context):
        def read_signature_arg(arg):
            return types.func_arg(
                arg.name,
                self._infer(arg.type, context).type,
            )
        
        if node.signature.returns is None:
            return_type = types.none_type
        else:
            return_type = self._infer(node.signature.returns, context).type
            
        return types.func(
            [read_signature_arg(arg) for arg in node.signature.args],
            return_type
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


    def _check_expression_statement(self, node, context):
        self._infer(node.value, context)


    def _check_return(self, node, context):
        expected = context.return_type
        actual = self._infer(node.value, context)
        if not types.is_sub_type(expected, actual):
            raise errors.TypeMismatchError(node, expected, actual)


    def _check_assignment(self, node, context):
        value_type = self._infer(node.value, context)
        for target in node.targets:
            self._assign(node, target, value_type, context)
    
    def _assign(self, node, target, value_type, context):
        if isinstance(target, nodes.VariableReference):
            self._assign_ref(node, target, value_type, context)
        elif isinstance(target, nodes.AttributeAccess):
            self._assign_attr(node, target, value_type, context)
        elif isinstance(target, nodes.Subscript):
            self._assign_subscript(node, target, value_type, context)
        else:
            raise Exception("Not implemented yet")
    
    
    def _assign_ref(self, node, target, value_type, context):
        var_type = context.lookup(target, allow_unbound=True)
        if var_type is not None and not types.is_sub_type(var_type, value_type):
            raise errors.BadAssignmentError(node, target_type=var_type, value_type=value_type)
        
        # TODO: add test demonstrating necessity of `if var_type is None`
        if var_type is None:
            context.update_type(target, value_type)
        
        if self._is_package() and context.is_module_scope:
            self._check_for_package_value_and_module_name_clashes(target, value_type)

    def _is_package(self):
        return self._module_path and os.path.basename(self._module_path) == "__init__.py"

    def _check_for_package_value_and_module_name_clashes(self, target, value_type):
        submodule = self._find_submodule(target.name)
        if submodule is not None:
            if value_type is not submodule:
                raise errors.ImportedValueRedeclaration(target, target.name)


    def _assign_attr(self, node, target, value_type, context):
        target_type = self._infer(target, context)
        
        if not types.is_sub_type(target_type, value_type):
            raise errors.BadAssignmentError(target, value_type=value_type, target_type=target_type)
        
        obj_type = self._infer(target.value, context)
        if obj_type.attrs.get(target.attr).read_only:
            raise errors.ReadOnlyAttributeError(target, obj_type, target.attr)
    
    def _assign_subscript(self, node, target, value_type, context):
        self._expression_type_inferer.infer_magic_method_call(
            node,
            "setitem",
            target.value,
            [target.slice, ephemeral.formal_arg_constraint(value_type)],
            context,
        )
    
    
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
        iterable_type = self._infer(node.iterable, context)
        if "__iter__" in iterable_type.attrs:
            iterator_type = self._expression_type_inferer.infer_magic_method_call(node, "iter", node.iterable, [], context)
            if not types.iterator.is_instantiated_type(iterator_type):
                raise errors.BadSignatureError(node.iterable, "__iter__ should return an iterator")
            
            element_type, = iterator_type.params
            return element_type
        elif "__getitem__" in iterable_type.attrs:
            args = [ephemeral.formal_arg_constraint(types.int_type)]
            return self._expression_type_inferer.infer_magic_method_call(node, "getitem", node.iterable, args, context)
        else:
            raise errors.TypeMismatchError(node.iterable, expected="iterable type", actual=iterable_type)
    
    
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
            meta_type = self._infer(handler.type, context)
            if not types.is_meta_type(meta_type) or not types.is_sub_type(types.exception_type, meta_type.type):
                raise errors.TypeMismatchError(handler.type,
                    expected="exception type",
                    actual=meta_type,
                )
            return meta_type.type
    
    
    def _check_raise(self, node, context):
        exception_type = self._infer(node.value, context)
        if not types.is_sub_type(types.exception_type, exception_type):
            raise errors.TypeMismatchError(
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
        
        exit_return_type = self._infer_magic_method_call(
            node.value,
            "exit",
            node.value,
            [
                ephemeral.formal_arg_constraint(type_)
                for type_ in [types.exception_meta_type, types.exception_type, types.traceback_type]
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
        # TODO: handle absolute imports
        if names[0] not in [".", ".."] and not self._is_executable:
            raise errors.ImportError(node, "Absolute imports not yet implemented")
            
        package_path, module_path = self._possible_module_paths(names)
        
        package_value = self._source_tree.import_module(package_path)
        module_value = self._source_tree.import_module(module_path)
        
        if package_value is not None and module_value is not None:
            raise errors.ImportError(node,
                "Import is ambiguous: the module '{0}.py' and the package '{0}/__init__.py' both exist".format(
                    names[-1])
            )
        elif package_value is None and module_value is None:
            raise errors.ModuleNotFoundError(node, "Could not find module '{}'".format(".".join(names)))
        else:
            return package_value or module_value

    def _possible_module_paths(self, names):
        import_path = os.path.normpath(os.path.join(os.path.dirname(self._module_path), *names))
        
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
