from .. import nodes, types, errors
from . import ephemeral


class ExpressionTypeInferer(object):
    def __init__(self, type_lookup):
        self._type_lookup = type_lookup
        
        self._inferers = {
            nodes.NoneExpression: self._infer_none,
            nodes.BooleanExpression: self._infer_bool,
            nodes.IntExpression: self._infer_int,
            nodes.StringExpression: self._infer_str,
            nodes.ListExpression: self._infer_list,
            nodes.VariableReference: self._infer_ref,
            nodes.Call: self._infer_call,
            nodes.AttributeAccess: self._infer_attr,
            nodes.BinaryOperation: self._infer_binary_operation,
            nodes.UnaryOperation: self._infer_unary_operation,
            nodes.Subscript: self._infer_subscript,
            ephemeral.EphemeralNode: lambda node, context: self.infer(node._node, context),
            ephemeral.FormalArgumentConstraint: lambda node, context: node.type,
        }
    
    def infer(self, expression, context):
        expression_type = self._inferers[type(expression)](expression, context)
        self._type_lookup[id(expression)] = expression_type
        return expression_type
    
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
        if not context.has_name(node.name):
            raise errors.UndefinedNameError(node, node.name)
            
        if not context.is_bound(node.name):
            raise errors.UnboundLocalError(node, node.name)
            
        return context.lookup(node.name)

    def _infer_call(self, node, context):
        call_type = self.get_call_type(node.func, context)
        self.type_check_args(node, node.args, call_type.params[:-1], context)
        return call_type.params[-1]

    def get_call_type(self, node, context):
        callee_type = self.infer(node, context)
        if types.func_type.is_instantiated_type(callee_type):
            return callee_type
        elif "__call__" in callee_type.attrs:
            return self.get_call_type(ephemeral.attr(node, "__call__"), context)
        else:
            raise errors.TypeMismatchError(node, expected="callable object", actual=callee_type)


    def _infer_attr(self, node, context):
        value_type = self.infer(node.value, context)
        if node.attr in value_type.attrs:
            return value_type.attrs.type_of(node.attr)
        else:
            raise errors.NoSuchAttributeError(node, str(value_type), node.attr)


    def _infer_binary_operation(self, node, context):
        return self.infer_magic_method_call(node, node.operator, node.left, [node.right], context)
    
    def _infer_unary_operation(self, node, context):
        return self.infer_magic_method_call(node, node.operator, node.operand, [], context)
    
    def _infer_subscript(self, node, context):
        return self.infer_magic_method_call(node, "getitem", node.value, [node.slice], context)
    
    def infer_magic_method_call(self, node, short_name, receiver, actual_args, context):
        method_name = "__{}__".format(short_name)
        method = self._get_method_type(receiver, method_name, context)
        
        formal_arg_types = method.params[:-1]
        formal_return_type = method.params[-1]
        
        if len(formal_arg_types) != len(actual_args):
            raise errors.BadSignatureError(receiver, "{} should have exactly {} argument(s)".format(method_name, len(actual_args)))
        
        self.type_check_args(node, actual_args, formal_arg_types, context)
        
        return formal_return_type
    
    def _get_method_type(self, receiver, method_name, context):
        receiver_type = self.infer(receiver, context)
        
        if method_name not in receiver_type.attrs:
            raise errors.TypeMismatchError(receiver, expected="object with method '{}'".format(method_name), actual=receiver_type)
        
        return self.get_call_type(ephemeral.attr(receiver, method_name), context)
    
    def type_check_args(self, node, actual_args, formal_arg_types, context):
        if len(formal_arg_types) != len(actual_args):
            raise errors.ArgumentsLengthError(
                node,
                expected=len(formal_arg_types),
                actual=len(actual_args)
            )
            
        for actual_arg, formal_arg_type in zip(actual_args, formal_arg_types):
            actual_arg_type = self.infer(actual_arg, context)
            if not types.is_sub_type(formal_arg_type, actual_arg_type):
                if isinstance(actual_arg, ephemeral.FormalArgumentConstraint):
                    raise errors.TypeMismatchError(
                        actual_arg.formal_arg_node,
                        expected=actual_arg_type,
                        actual=formal_arg_type
                    )
                else:
                    raise errors.TypeMismatchError(
                        actual_arg,
                        expected=formal_arg_type,
                        actual=actual_arg_type
                    )
