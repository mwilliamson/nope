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
        return context.lookup(node)

    def _infer_call(self, node, context):
        def read_actual_arg(actual_arg, index):
            if isinstance(actual_arg, ephemeral.FormalArgumentConstraint) and actual_arg.formal_arg_node is None:
                return ephemeral.formal_arg_constraint(ephemeral.formal_arg(node.func, index), actual_arg.type)
            else:
                return actual_arg
        
        call_function_type = self._get_call_type(node.func, context)
        
        if len(node.args) > len(call_function_type.args):
            raise errors.ArgumentsError(
                node,
                "function takes {} positional arguments but {} was given".format(
                    len(call_function_type.args),
                    len(node.args))
            )
        
        formal_arg_types = [
            arg.type
            for arg in call_function_type.args
        ]
        
        kwarg_nodes = node.kwargs.copy()
        actual_args = []
        
        for index, formal_arg in enumerate(call_function_type.args):
            positional_arg = None
            keyword_arg = None
            
            if index < len(node.args):
                positional_arg = node.args[index]
            if formal_arg.name is not None:
                keyword_arg = kwarg_nodes.pop(formal_arg.name, None)
            
            if positional_arg is not None and keyword_arg is not None:
                raise errors.ArgumentsError(node, "multiple values for argument '{}'".format(formal_arg.name))
            elif positional_arg is not None:
                actual_args.append(read_actual_arg(positional_arg, index))
            elif keyword_arg is not None:
                actual_args.append(read_actual_arg(keyword_arg, index))
            else:
                if formal_arg.name is None:
                    message = "missing {} positional argument".format(_ordinal(index + 1))
                else:
                    message = "missing argument '{}'".format(formal_arg.name)
                raise errors.ArgumentsError(node, message)
        
        if kwarg_nodes:
            first_key = next(iter(kwarg_nodes.keys()))
            raise errors.ArgumentsError(node, "unexpected keyword argument '{}'".format(first_key))
        
        self._type_check_args(
            node,
            actual_args,
            formal_arg_types,
            context
        )
        return call_function_type.return_type

    def _get_call_type(self, node, context):
        callee_type = self.infer(node, context)
        if types.is_func_type(callee_type):
            return callee_type
        elif "__call__" in callee_type.attrs:
            return self._get_call_type(ephemeral.attr(node, "__call__"), context)
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
        
        formal_arg_types = [arg.type for arg in method.args]
        
        # TODO: check keyword arguments
        if len(formal_arg_types) != len(actual_args):
            raise errors.BadSignatureError(receiver, "{} should have exactly {} argument(s)".format(method_name, len(actual_args)))
        
        call_node = ephemeral.call(
            node,
            ephemeral.attr(receiver, method_name),
            actual_args,
        )
        return self._infer_call(call_node, context)
    
    def _get_method_type(self, receiver, method_name, context):
        receiver_type = self.infer(receiver, context)
        
        if method_name not in receiver_type.attrs:
            raise errors.TypeMismatchError(receiver, expected="object with method '{}'".format(method_name), actual=receiver_type)
        
        return self._get_call_type(ephemeral.attr(receiver, method_name), context)
    
    def _type_check_args(self, node, actual_args, formal_arg_types, context):
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


_ordinal_suffixes = {1: "st", 2: "nd", 3: "rd"}

def _ordinal(num):
    if 10 <= num % 100 <= 20:
        suffix = "th"
    else:
        suffix = _ordinal_suffixes.get(num % 10, "th")
    
    return "{}{}".format(num, suffix)
