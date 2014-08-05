import os

from . import types, nodes, util, errors, returns
from .context import new_module_context


def check(module, source_tree=None, module_path=None):
    checker = TypeChecker(source_tree, module_path, module.is_executable)
    return checker.check(module)

def infer(expression, context, source_tree=None, module_path=None):
    checker = TypeChecker(source_tree, module_path, False)
    return checker.infer(expression, context)

def update_context(statement, context, source_tree=None, module_path=None, is_executable=False):
    checker = TypeChecker(source_tree, module_path, is_executable)
    return checker.update_context(statement, context)


class TypeChecker(object):
    def __init__(self, source_tree, module_path, is_executable):
        self._source_tree = source_tree
        self._module_path = module_path
        self._is_executable = is_executable

    def infer(self, expression, context):
        return self._inferers[type(expression)](self, expression, context)

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
        
        if len(func_type.params) - 1 != len(node.args):
            raise errors.ArgumentsLengthError(
                node,
                expected=len(func_type.params) - 1,
                actual=len(node.args)
            )
        
        for actual_arg, formal_arg_type in zip(node.args, func_type.params[:-1]):
            actual_arg_type = self.infer(actual_arg, context)
            if not types.is_sub_type(formal_arg_type, actual_arg_type):
                raise errors.TypeMismatchError(
                    actual_arg,
                    expected=formal_arg_type,
                    actual=actual_arg_type
                )
        
        return self.infer(node.func, context).params[-1]


    def _infer_attr(self, node, context):
        value_type = self.infer(node.value, context)
        if node.attr in value_type.attrs:
            return value_type.attrs[node.attr]
        else:
            raise errors.AttributeError(node, value_type.name, node.attr)
    
    def _infer_binary_operation(self, node, context):
        left_type = self.infer(node.left, context)
        
        # TODO: check argument and return type
        if "__add__" not in left_type.attrs:
            raise errors.TypeMismatchError(node, expected="Type with __add__", actual=left_type)
            
        add_func = left_type.attrs["__add__"]
        if add_func.params[:-1] != [left_type]:
            raise errors.BadSignatureError(node, "Argument of __add__ should accept own type")
        
        right_type = self.infer(node.right, context)
        # This is a significant simplication of the rules in Python.
        # We use equality instead of subtyping to maintain symmetry
        if left_type != right_type:
            raise errors.TypeMismatchError(node, expected=left_type, actual=right_type)
        
        return left_type


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
        for name in node.targets:
            context.add(node, name, value_type)
    
    
    def _check_if_else(self, node, context):
        self.infer(node.condition, context)
        
        true_context = context.enter_block()
        for statement in node.true_body:
            self.update_context(statement, true_context)
        
        false_context = context.enter_block()
        for statement in node.false_body:
            self.update_context(statement, false_context)
        
        context.unify([true_context, false_context])
    

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
        

    _checkers = {
        nodes.ExpressionStatement: _check_expression_statement,
        nodes.ReturnStatement: _check_return,
        nodes.Assignment: _check_assignment,
        nodes.IfElse: _check_if_else,
        nodes.FunctionDef: _check_function_def,
        nodes.Import: _check_import,
        nodes.ImportFrom: _check_import_from,
    }
