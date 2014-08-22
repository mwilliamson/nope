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
        
        return_type = read_annotation(node.signature.returns)
            
        return types.func(
            [read_annotation(arg) for arg in node.signature.args],
            return_type
        )

    def _check_function_def(self, node, context):
        func_type = self._infer_function_def(node, context)
        return_type = func_type.return_type
        
        arg_names = [arg.name for arg in node.args.args]
        
        local_names = arg_names + list(util.declared_locals(node.body))
        
        body_context = context.enter_func(return_type, local_names=local_names)
        
        for arg, arg_type in zip(node.args.args, func_type.args):
            body_context.add(arg.name, arg_type)
            
        self.update_context(node.body, body_context)
        
        if return_type != types.none_type and not returns.has_unconditional_return(node.body):
            raise errors.MissingReturnError(node, return_type)
        
        context.add(node.name, func_type)


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
        var_type = context.lookup(target.name, allow_unbound=True)
        if var_type is not None and not types.is_sub_type(var_type, value_type):
            raise errors.BadAssignmentError(node, target_type=var_type, value_type=value_type)
        
        if not context.is_bound(target.name):
            context.add(target.name, value_type)


    def _assign_attr(self, node, target, value_type, context):
        target_type = self._infer(target, context)
        
        if not types.is_sub_type(target_type, value_type):
            raise errors.BadAssignmentError(target, value_type=value_type, target_type=target_type)
        
        obj_type = self._infer(target.value, context)
        if obj_type.attrs.get(target.attr).read_only:
            raise errors.ReadOnlyAttributeError(target, obj_type, target.attr)
    
    def _assign_subscript(self, node, target, value_type, context):
        setitem_node = ephemeral.attr(target.value, "__setitem__")
        setitem_type = self._expression_type_inferer.get_call_type(setitem_node, context)
        self._expression_type_inferer.type_check_args(
            node,
            # TODO: use ephemeral node to represent formal argument of __setitem__
            [target.slice, ephemeral.formal_arg_constraint(setitem_node, value_type)],
            setitem_type.args,
            context,
        )
    
    
    def _check_if_else(self, node, context):
        self._infer(node.condition, context)
        
        self._check_branches(
            [
                _IfElseBranch(node.true_body),
                _IfElseBranch(node.false_body),
            ],
            context,
            bind=True,
        )


    def _check_while_loop(self, node, context):
        self._infer(node.condition, context)
        self._check_branches(
            [
                _LoopBranch(node.body),
                _LoopBranch(node.else_body),
            ],
            context,
            bind=False,
        )
    
    
    def _check_for_loop(self, node, context):
        element_type = self._infer_for_loop_element_type(node, context)
        
        def assign_loop_target(body_context):
            self._assign(node, node.target, element_type, body_context)
        
        self._check_branches(
            [
                _LoopBranch(node.body, before=assign_loop_target),
                _LoopBranch(node.else_body),
            ],
            context,
            bind=False,
        )
    
    
    def _check_branches(self, branches, context, bind):
        def check_branch(branch):
            branch_context = branch.enter_context(context)
            self.update_context(branch.statements, branch_context)
            return branch_context
        
        contexts = list(map(check_branch, branches))
        
        context.unify(contexts, bind=bind)
    
    
    def _infer_for_loop_element_type(self, node, context):
        iterable_type = self._infer(node.iterable, context)
        if "__iter__" in iterable_type.attrs:
            iterator_type = self._expression_type_inferer.infer_magic_method_call(node, "iter", node.iterable, [], context)
            if not types.iterator.is_instantiated_type(iterator_type):
                raise errors.BadSignatureError(node.iterable, "__iter__ should return an iterator")
            
            element_type, = iterator_type.params
            return element_type
        elif "__getitem__" in iterable_type.attrs:
            args = [ephemeral.formal_arg_constraint(ephemeral.attr(node.iterable, "__getitem__"), types.int_type)]
            return self._expression_type_inferer.infer_magic_method_call(node, "getitem", node.iterable, args, context)
        else:
            raise errors.TypeMismatchError(node.iterable, expected="iterable type", actual=iterable_type)
    
    
    def _check_break(self, node, context):
        self._check_loop_control_statement("break", node, context)
    
    
    def _check_continue(self, node, context):
        self._check_loop_control_statement("continue", node, context)
    
        
    def _check_loop_control_statement(self, name, node, context):
        if not context.in_loop:
            raise errors.InvalidStatementError(node, "'{}' outside loop".format(name))
    
    
    def _check_try(self, node, context):
        def infer_handler_exception_type(handler):
            if handler.type:
                meta_type = self._infer(handler.type, context)
                if not types.is_meta_type(meta_type) or not types.is_sub_type(types.exception_type, meta_type.type):
                    raise errors.TypeMismatchError(handler.type,
                        expected="exception type",
                        actual=meta_type,
                    )
                return meta_type
        
        handler_exception_types = [
            infer_handler_exception_type(handler)
            for handler in node.handlers
        ]
        
        def create_except_branch(handler, exception_type):
            if handler.name:
                before = lambda branch_context: branch_context.add(handler.name, exception_type)
            else:
                before = None
            return _Branch(handler.body, before=before)
        
        
        except_branches = [
            create_except_branch(handler, exception_type)
            for handler, exception_type in zip(node.handlers, handler_exception_types)
        ]
        
        self._check_branches(
            [_Branch(node.body)] + except_branches,
            context,
            bind=False,
        )
        self.update_context(node.finally_body, context)
    
    
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
                # TODO: use ephemeral nodes to represent formal args of __exit__
                ephemeral.formal_arg_constraint(node.value, type_)
                for type_ in [types.exception_meta_type, types.exception_type, types.traceback_type]
            ],
            context,
        )
        
        def assign_target(branch_context):
            if node.target is not None:
                self._assign(node.target, node.target, enter_return_type, branch_context)
        
        self._check_branches(
            [
                _Branch(node.body, before=assign_target),
            ],
            context,
            bind=exit_return_type == types.none_type,
        )

    def _check_import(self, node, context):
        for alias in node.names:
            if alias.asname is None:
                parts = alias.name_parts
                
                for index, part in enumerate(parts):
                    this_module = self._find_module(node, parts[:index + 1])
                    
                    if index == 0:
                        context.add(part, this_module)
                    else:
                        # TODO: set readonly
                        last_module.attrs.add(part, this_module)
                        
                    last_module = this_module
                
            else:
                module = self._find_module(node, alias.name_parts)
                context.add(alias.value_name, module)


    def _check_import_from(self, node, context):
        module = self._find_module(node, node.module)
        for alias in node.names:
            module_value = module.attrs.type_of(alias.name)
            if module_value is not None:
                context.add(alias.value_name, module_value)
            else:
                submodule = self._find_module(node, node.module + [alias.name])
                # TODO: set readonly
                module.attrs.add(alias.value_name, submodule)
                context.add(alias.value_name, submodule)

    
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


class _LoopBranch(object):
    def __init__(self, statements, before=None):
        self.statements = statements
        self.before = before
    
    def enter_context(self, context):
        loop_context = context.enter_loop()
        if self.before is not None:
            self.before(loop_context)
        return loop_context

class _Branch(object):
    def __init__(self, statements, before=None):
        self.statements = statements
        self.before = before
        
    def enter_context(self, context):
        branch_context = context.enter_branch()
        if self.before is not None:
            self.before(branch_context)
        return branch_context
    
_IfElseBranch = _Branch
