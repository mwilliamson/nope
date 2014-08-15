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
            nodes.RaiseStatement: self._check_raise,
            nodes.FunctionDef: self._check_function_def,
            nodes.Import: self._check_import,
            nodes.ImportFrom: self._check_import_from,
        }

    def update_context(self, statement, context):
        self._checkers[type(statement)](statement, context)
        
        if self._is_package() and context.is_module_scope:
            self._check_for_package_value_and_module_name_clashes(statement, context)

    def _is_package(self):
        return self._module_path and os.path.basename(self._module_path) == "__init__.py"

    def _check_for_package_value_and_module_name_clashes(self, statement, context):
        for declared_name in util.declared_names(statement):
            submodule = self._find_submodule(declared_name)
            if submodule is not None:
                if context.lookup(declared_name) is not submodule:
                    raise errors.ImportedValueRedeclaration(statement, declared_name)

    def _find_submodule(self, name):
        for path in self._possible_module_paths([".", name]):
            if path in self._source_tree:
                return self._source_tree.import_module(path)
        
        return None
    
    def _infer_function_def(self, node, context):
        def read_annotation(annotation):
            if annotation is None:
                return types.none_type
            else:
                result = self._infer(annotation, context)
                return result.type
        
        return_type = read_annotation(node.return_annotation)
            
        return types.func(
            [read_annotation(arg.annotation) for arg in node.args.args],
            return_type
        )

    def _check_function_def(self, node, context):
        func_type = self._infer_function_def(node, context)
        return_type = func_type.params[-1]
        
        arg_names = [arg.name for arg in node.args.args]
        
        local_names = arg_names + list(util.declared_locals(node.body))
        
        body_context = context.enter_func(return_type, local_names=local_names)
        
        for arg, arg_type in zip(node.args.args, func_type.params):
            body_context.add(arg, arg.name, arg_type)
            
        for statement in node.body:
            self.update_context(statement, body_context)
        
        if return_type != types.none_type and not returns.has_unconditional_return(node.body):
            raise errors.MissingReturnError(node, return_type)
        
        context.add(node, node.name, func_type)


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
            # TODO: should we pass target in instead of node?
            var_type = context.lookup(target.name, allow_unbound=True)
            if var_type is not None and not types.is_sub_type(var_type, value_type):
                raise errors.TypeMismatchError(node, expected=var_type, actual=value_type)
            
            if not context.is_bound(target.name):
                context.add(node, target.name, value_type)
            
        elif isinstance(target, nodes.Subscript):
            setitem_node = ephemeral.attr(target.value, "__setitem__")
            setitem_type = self._expression_type_inferer.get_call_type(setitem_node, context)
            self._expression_type_inferer.type_check_args(
                node,
                # TODO: use ephemeral node to represent formal argument of __setitem__
                [target.slice, ephemeral.formal_arg_constraint(setitem_node, value_type)],
                setitem_type.params[:-1],
                context,
            )
        else:
            raise Exception("Not implemented yet")
    
    
    def _check_if_else(self, node, context):
        self._infer(node.condition, context)
        
        true_context = context.enter_if_else_branch()
        for statement in node.true_body:
            self.update_context(statement, true_context)
        
        false_context = context.enter_if_else_branch()
        for statement in node.false_body:
            self.update_context(statement, false_context)
        
        context.unify([true_context, false_context], bind=True)


    def _check_while_loop(self, node, context):
        self._infer(node.condition, context)
        
        body_context = context.enter_loop()
        for statement in node.body:
            self.update_context(statement, body_context)
        
        else_body_context = context.enter_loop()
        for statement in node.else_body:
            self.update_context(statement, else_body_context)
            
        context.unify([body_context, else_body_context], bind=False)
    
    
    def _check_for_loop(self, node, context):
        iterable_type = self._infer(node.iterable, context)
        if "__iter__" in iterable_type.attrs:
            iterator_type = self._expression_type_inferer.infer_magic_method_call(node, "iter", node.iterable, [], context)
            if not types.iterator.is_instantiated_type(iterator_type):
                raise errors.BadSignatureError(node.iterable, "__iter__ should return an iterator")
            
            element_type, = iterator_type.params
        elif "__getitem__" in iterable_type.attrs:
            element_type = self._expression_type_inferer.infer_magic_method_call(node, "getitem", node.iterable, [nodes.int(0)], context)
        else:
            raise errors.TypeMismatchError(node.iterable, expected="iterable type", actual=iterable_type)
        
        body_context = context.enter_loop()
        self._assign(node, node.target, element_type, body_context)
        for statement in node.body:
            self.update_context(statement, body_context)
        
        else_body_context = context.enter_loop()
        for statement in node.else_body:
            self.update_context(statement, else_body_context)
        
        context.unify([body_context, else_body_context], bind=False)
    
    
    def _check_break(self, node, context):
        self._check_loop_control_statement("break", node, context)
    
    
    def _check_continue(self, node, context):
        self._check_loop_control_statement("continue", node, context)
    
        
    def _check_loop_control_statement(self, name, node, context):
        if not context.in_loop:
            raise errors.InvalidStatementError(node, "'{}' outside loop".format(name))
    
    
    def _check_raise(self, node, context):
        exception_type = self._infer(node.value, context)
        if not types.is_sub_type(types.exception_type, exception_type):
            raise errors.TypeMismatchError(
                node.value,
                expected=types.exception_type,
                actual=exception_type,
            )
    

    def _check_import(self, node, context):
        for alias in node.names:
            if alias.asname is None:
                parts = alias.name_parts
                
                for index, part in enumerate(parts):
                    this_module = self._find_module(node, parts[:index + 1])
                    
                    if index == 0:
                        context.add(node, part, this_module)
                    else:
                        last_module.attrs[part] = this_module
                        
                    last_module = this_module
                
            else:
                module = self._find_module(node, alias.name_parts)
                context.add(node, alias.value_name, module)


    def _check_import_from(self, node, context):
        module = self._find_module(node, node.module)
        for alias in node.names:
            module_value = module.attrs.get(alias.name)
            if module_value is not None:
                context.add(node, alias.value_name, module_value)
            else:
                submodule = self._find_module(node, node.module + [alias.name])
                module.attrs[alias.value_name] = submodule
                context.add(node, alias.value_name, submodule)

    
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
