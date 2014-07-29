import os

from . import types, nodes, util
from .context import new_module_context


def check(module, source_tree=None, module_path=None):
    checker = TypeChecker(source_tree, module_path)
    return checker.check(module)

def infer(expression, context, source_tree=None, module_path=None):
    checker = TypeChecker(source_tree, module_path)
    return checker.infer(expression, context)

def update_context(statement, context, source_tree=None, module_path=None):
    checker = TypeChecker(source_tree, module_path)
    return checker.update_context(statement, context)


class TypeChecker(object):
    def __init__(self, source_tree, module_path):
        self._source_tree = source_tree
        self._module_path = module_path

    def infer(self, expression, context):
        return self._inferers[type(expression)](self, expression, context)

    def update_context(self, statement, context, source_tree=None):
        return self._checkers[type(statement)](self, statement, context)

    def check(self, module):
        export_names = []
        
        context = new_module_context()
        for statement in module.body:
            self.update_context(statement, context)
            if isinstance(statement, nodes.Assignment):
                if "__all__" in statement.targets:
                    assert isinstance(statement.value, nodes.StringExpression)
                    export_names = statement.value.value.split(",")
        
        return Module(dict(
            (name, context.lookup(name))
            for name in export_names
        ))


    def _infer_none(self, node, context):
        return types.none_type

    def _infer_int(self, node, context):
        return types.int

    def _infer_str(self, node, context):
        return types.str

    def _infer_ref(self, node, context):
        ref_type = context.lookup(node.name)
        if ref_type is None:
            raise UnboundLocalError(node, node.name)
        else:
            return ref_type

    def _infer_call(self, node, context):
        func_type = self.infer(node.func, context)
        
        if len(func_type.params) - 1 != len(node.args):
            raise ArgumentsLengthError(node, expected=len(func_type.params) - 1, actual=len(node.args))
        
        for actual_arg, formal_arg_type in zip(node.args, func_type.params[:-1]):
            actual_arg_type = self.infer(actual_arg, context)
            if not types.is_sub_type(formal_arg_type, actual_arg_type):
                raise TypeMismatchError(actual_arg, expected=formal_arg_type, actual=actual_arg_type)
        
        return self.infer(node.func, context).params[-1]


    def _infer_attr(self, node, context):
        value_type = self.infer(node.value, context)
        if node.attr in value_type.attrs:
            return value_type.attrs[node.attr]
        else:
            raise AttributeError(node, value_type.name, node.attr)


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
        
        local_names = arg_names + util.declared_locals(node)
        
        body_context = context.enter_func(return_type, local_names=local_names)
        
        for arg, arg_type in zip(node.args.args, func_type.params):
            body_context.add(arg.name, arg_type)
            
        for statement in node.body:
            self.update_context(statement, body_context)
            
        context.add(node.name, func_type)
        

    _inferers = {
        nodes.NoneExpression: _infer_none,
        nodes.IntExpression: _infer_int,
        nodes.StringExpression: _infer_str,
        nodes.VariableReference: _infer_ref,
        nodes.Call: _infer_call,
        nodes.AttributeAccess: _infer_attr,
    }


    def _check_expression_statement(self, node, context):
        self.infer(node.value, context)


    def _check_return(self, node, context):
        expected = context.return_type
        actual = self.infer(node.value, context)
        if not types.is_sub_type(expected, actual):
            raise TypeMismatchError(node, expected, actual)


    def _check_assignment(self, node, context):
        value_type = self.infer(node.value, context)
        for name in node.targets:
            context.add(name, value_type)


    def _check_import_from(self, node, context):
        # TODO: handle absolute imports
        # TODO: handle failures properly (ImportError.message and .node)
        import_path = os.path.join(os.path.dirname(self._module_path), *node.module)
        import_path = os.path.join(import_path, "__init__.py")
        
        try:
            module = self._source_tree.check(os.path.abspath(import_path))
        except KeyError:
            raise ImportError()
        
        # TODO: handle aliases
        for alias in node.names:
            name = alias.name
            context.add(name, module.exports[name])


    _checkers = {
        nodes.ExpressionStatement: _check_expression_statement,
        nodes.ReturnStatement: _check_return,
        nodes.Assignment: _check_assignment,
        nodes.FunctionDef: _check_function_def,
        nodes.ImportFrom: _check_import_from,
    }


class Module(object):
    def __init__(self, exports):
        self.exports = exports


class TypeCheckError(Exception):
    pass


class ArgumentsLengthError(TypeCheckError):
    def __init__(self, node, expected, actual):
        self.node = node
        self.expected = expected
        self.actual = actual


class TypeMismatchError(TypeCheckError):
    def __init__(self, node, expected, actual):
        self.expected = expected
        self.actual = actual
        self.node = node
        
    def __str__(self):
        return "Expected {0} but was {1}".format(self.expected, self.actual)


class UnboundLocalError(TypeCheckError):
    def __init__(self, node, name):
        self.node = node
        self.name = name
    
    def __str__(self):
        return "local variable {0} referenced before assignment".format(self.name)


class AttributeError(TypeCheckError):
    def __init__(self, node, obj_type, attr_name):
        self.node = node
        self._obj_type = obj_type
        self._attr_name = attr_name
    
    def __str__(self):
        return "{} object has no attribute {}".format(self._obj_type, self._attr_name)


class ImportError(TypeCheckError):
    pass
