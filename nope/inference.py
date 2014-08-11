import os

from . import types, nodes, util, errors, returns
from .context import new_module_context


def check(module, source_tree=None, module_path=None):
    checker = _TypeChecker(source_tree, module_path, module.is_executable)
    module_type = checker.check(module)
    return module_type, checker.type_lookup()

def infer(expression, context, source_tree=None, module_path=None):
    checker = _TypeChecker(source_tree, module_path, False)
    return checker.infer(expression, context)

def update_context(statement, context, source_tree=None, module_path=None, is_executable=False):
    checker = _TypeChecker(source_tree, module_path, is_executable)
    return checker.update_context(statement, context)


class _TypeChecker(object):
    def __init__(self, source_tree, module_path, is_executable):
        self._source_tree = source_tree
        self._module_path = module_path
        self._is_executable = is_executable
        self._type_lookup = {}
    
    def type_lookup(self):
        return types.TypeLookup(self._type_lookup)

    def infer(self, expression, context):
        expression_type = self._inferers[type(expression)](self, expression, context)
        self._type_lookup[id(expression)] = expression_type
        return expression_type

    def update_context(self, statement, context, source_tree=None):
        self._checkers[type(statement)](self, statement, context)
        
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
    

    def check(self, module):
        context = new_module_context(util.declared_locals(module.body))
        for statement in module.body:
            self.update_context(statement, context)
        
        return types.Module(self._module_path, dict(
            (name, context.lookup(name))
            for name in util.exported_names(module)
        ))


    def _infer_none(self, node, context):
        return types.none_type
    
    def _infer_bool(self, node, context):
        return types.boolean_type
    
    def _infer_int(self, node, context):
        return types.int_type

    def _infer_str(self, node, context):
        return types.str_type

    def _infer_list(self, node, context):
        element_types = [self.infer(element, context) for element in node.elements]
        return types.list_type(types.unify(element_types))

    def _infer_ref(self, node, context):
        try:
            ref_type = context.lookup(node.name)
        except KeyError:
            raise errors.UndefinedNameError(node, node.name)
        if ref_type is None:
            raise errors.UnboundLocalError(node, node.name)
        else:
            return ref_type

    def _infer_call(self, node, context):
        func_type = self.infer(node.func, context)
        self._type_check_args(node, node.args, func_type.params[:-1], context)
        return self.infer(node.func, context).params[-1]


    def _infer_attr(self, node, context):
        value_type = self.infer(node.value, context)
        if node.attr in value_type.attrs:
            return value_type.attrs[node.attr]
        else:
            raise errors.AttributeError(node, str(value_type), node.attr)
    
    def _infer_binary_operation(self, node, context):
        return self._read_magic_method(node, node.operator, node.left, [node.right], context)
    
    def _infer_unary_operation(self, node, context):
        return self._read_magic_method(node, node.operator, node.operand, [], context)
    
    def _infer_subscript(self, node, context):
        return self._read_magic_method(node, "getitem", node.value, [node.slice], context)
    
    def _read_magic_method(self, node, short_name, receiver, actual_args, context):
        method_name = "__{}__".format(short_name)
        receiver_type = self.infer(receiver, context)
        
        if method_name not in receiver_type.attrs:
            raise errors.TypeMismatchError(receiver, expected="type with {}".format(method_name), actual=receiver_type)
        
        method = receiver_type.attrs[method_name]
        formal_arg_types = method.params[:-1]
        formal_return_type = method.params[-1]
        
        if len(formal_arg_types) != len(actual_args):
            raise errors.BadSignatureError(receiver, "{} should have exactly {} argument(s)".format(method_name, len(actual_args)))
        
        self._type_check_args(node, actual_args, formal_arg_types, context)
        
        return formal_return_type
    
    def _type_check_args(self, node, actual_args, formal_arg_types, context):
        actual_args_with_types = [
            (actual_arg, self.infer(actual_arg, context))
            for actual_arg in actual_args
        ]
        return self._type_check_arg_types(node, actual_args_with_types, formal_arg_types)
        
    def _type_check_arg_types(self, node, actual_args_with_types, formal_arg_types):
        if len(formal_arg_types) != len(actual_args_with_types):
            raise errors.ArgumentsLengthError(
                node,
                expected=len(formal_arg_types),
                actual=len(actual_args_with_types)
            )
            
        for (actual_arg, actual_arg_type), formal_arg_type in zip(actual_args_with_types, formal_arg_types):
            if not types.is_sub_type(formal_arg_type, actual_arg_type):
                raise errors.TypeMismatchError(
                    actual_arg,
                    expected=formal_arg_type,
                    actual=actual_arg_type
                )
        


    def _infer_function_def(self, node, context):
        def read_annotation(annotation):
            if annotation is None:
                return types.none_type
            else:
                result = self.infer(annotation, context)
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
    

    _inferers = {
        nodes.NoneExpression: _infer_none,
        nodes.BooleanExpression: _infer_bool,
        nodes.IntExpression: _infer_int,
        nodes.StringExpression: _infer_str,
        nodes.ListExpression: _infer_list,
        nodes.VariableReference: _infer_ref,
        nodes.Call: _infer_call,
        nodes.AttributeAccess: _infer_attr,
        nodes.BinaryOperation: _infer_binary_operation,
        nodes.UnaryOperation: _infer_unary_operation,
        nodes.Subscript: _infer_subscript,
    }


    def _check_expression_statement(self, node, context):
        self.infer(node.value, context)


    def _check_return(self, node, context):
        expected = context.return_type
        actual = self.infer(node.value, context)
        if not types.is_sub_type(expected, actual):
            raise errors.TypeMismatchError(node, expected, actual)


    def _check_assignment(self, node, context):
        value_type = self.infer(node.value, context)
        for target in node.targets:
            self._assign(node, target, value_type, context)
    
    def _assign(self, node, target, value_type, context):
        if isinstance(target, nodes.VariableReference):
            # TODO: should we pass target in instead of node?
            context.add(node, target.name, value_type)
        elif isinstance(target, nodes.Subscript):
            target_value_type = self.infer(target.value, context)
            # TODO: check setitem exists and has correct signature
            setitem_type = target_value_type.attrs["__setitem__"]
            try:
                value_node = object()
                self._type_check_arg_types(
                    node,
                    [(target.slice, self.infer(target.slice, context)), (value_node, value_type)],
                    setitem_type.params[:-1],
                )
            except errors.TypeMismatchError as error:
                if error.node is value_node:
                    raise errors.TypeMismatchError(target, expected=error.actual, actual=error.expected)
                else:
                    raise
            
        else:
            raise Exception("Not implemented yet")
    
    
    def _check_if_else(self, node, context):
        self.infer(node.condition, context)
        
        true_context = context.enter_if_else_branch()
        for statement in node.true_body:
            self.update_context(statement, true_context)
        
        false_context = context.enter_if_else_branch()
        for statement in node.false_body:
            self.update_context(statement, false_context)
        
        context.unify([true_context, false_context])


    def _check_while_loop(self, node, context):
        self.infer(node.condition, context)
        
        for statement in node.body:
            self.update_context(statement, context)
    
    
    def _check_for_loop(self, node, context):
        iterable_type = self.infer(node.iterable, context)
        
        if "__iter__" not in iterable_type.attrs:
            raise errors.TypeMismatchError(node.iterable, expected="type with __iter__", actual=iterable_type)
        # TODO: check __iter__ signature
        
        iter_type = iterable_type.attrs["__iter__"]
        iterable_type, = iter_type.params
        element_type, = iterable_type.params
        
        body_context = context.enter_loop()
        self._assign(node, node.target, element_type, body_context)
        for statement in node.body:
            self.update_context(statement, body_context)
    
    
    def _check_break(self, node, context):
        self._check_loop_control_statement("break", node, context)
    
    
    def _check_continue(self, node, context):
        self._check_loop_control_statement("continue", node, context)
    
        
    def _check_loop_control_statement(self, name, node, context):
        if not context.in_loop:
            raise errors.InvalidStatementError(node, "'{}' outside loop".format(name))
    

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

    def _nop_check(self, node, context):
        pass
        

    _checkers = {
        nodes.ExpressionStatement: _check_expression_statement,
        nodes.ReturnStatement: _check_return,
        nodes.Assignment: _check_assignment,
        nodes.IfElse: _check_if_else,
        nodes.WhileLoop: _check_while_loop,
        nodes.ForLoop: _check_for_loop,
        nodes.BreakStatement: _check_break,
        nodes.ContinueStatement: _check_continue,
        nodes.FunctionDef: _check_function_def,
        nodes.Import: _check_import,
        nodes.ImportFrom: _check_import_from,
    }
