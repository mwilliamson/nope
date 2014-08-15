from .. import nodes, types, errors


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
        callee_type = self.infer(node.func, context)
        if types.func_type.is_instantiated_type(callee_type):
            func_type = callee_type
        else:
            call_method = self._get_magic_method(node.func, "call", context)
            if call_method is None:
                raise errors.TypeMismatchError(node.func, expected="callable object", actual=callee_type)
            else:
                func_type = call_method
            
        self._type_check_args(node, node.args, func_type.params[:-1], context)
        return func_type.params[-1]


    def _infer_attr(self, node, context):
        value_type = self.infer(node.value, context)
        if node.attr in value_type.attrs:
            return value_type.attrs[node.attr]
        else:
            raise errors.AttributeError(node, str(value_type), node.attr)


    def _infer_binary_operation(self, node, context):
        return self.infer_magic_method_call(node, node.operator, node.left, [node.right], context)
    
    def _infer_unary_operation(self, node, context):
        return self.infer_magic_method_call(node, node.operator, node.operand, [], context)
    
    def _infer_subscript(self, node, context):
        return self.infer_magic_method_call(node, "getitem", node.value, [node.slice], context)
    
    def infer_magic_method_call(self, node, short_name, receiver, actual_args, context):
        method_name = "__{}__".format(short_name)
        method = self._get_magic_method(receiver, short_name, context, required=True)
        
        formal_arg_types = method.params[:-1]
        formal_return_type = method.params[-1]
        
        if len(formal_arg_types) != len(actual_args):
            raise errors.BadSignatureError(receiver, "{} should have exactly {} argument(s)".format(method_name, len(actual_args)))
        
        self._type_check_args(node, actual_args, formal_arg_types, context)
        
        return formal_return_type
    
    def _get_magic_method(self, receiver, short_name, context, required=False):
        method_name = "__{}__".format(short_name)
        receiver_type = self.infer(receiver, context)
        
        if method_name not in receiver_type.attrs:
            if required:
                raise errors.TypeMismatchError(receiver, expected="type with {}".format(method_name), actual=receiver_type)
            else:
                return None
        
        method_type = receiver_type.attrs[method_name]
        
        if not types.func_type.is_instantiated_type(method_type):
            raise errors.BadSignatureError(receiver, "{} should be a method".format(method_name))
        
        return receiver_type.attrs[method_name]
    
    def _type_check_args(self, node, actual_args, formal_arg_types, context):
        actual_args_with_types = [
            (actual_arg, self.infer(actual_arg, context))
            for actual_arg in actual_args
        ]
        return self.type_check_arg_types(node, actual_args_with_types, formal_arg_types)
        
    def type_check_arg_types(self, node, actual_args_with_types, formal_arg_types):
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
