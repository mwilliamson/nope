from .. import nodes, types, errors
from . import ephemeral
from .assignment import Assignment


class ExpressionTypeInferer(object):
    def __init__(self, type_lookup):
        self._type_lookup = type_lookup
        
        self._inferers = {
            nodes.NoneExpression: self._infer_none,
            nodes.BooleanExpression: self._infer_bool,
            nodes.IntExpression: self._infer_int,
            nodes.StringExpression: self._infer_str,
            nodes.TupleLiteral: self._infer_tuple_literal,
            nodes.ListLiteral: self._infer_list_literal,
            nodes.DictLiteral: self._infer_dict_literal,
            nodes.VariableReference: self._infer_ref,
            nodes.Call: self._infer_call,
            nodes.AttributeAccess: self._infer_attr,
            nodes.TypeApplication: self._infer_type_application,
            nodes.BinaryOperation: self._infer_binary_operation,
            nodes.UnaryOperation: self._infer_unary_operation,
            nodes.Subscript: self._infer_subscript,
            nodes.Slice: self._infer_slice,
            nodes.ListComprehension: self._infer_list_comprehension,
            nodes.GeneratorExpression: self._infer_generator_expression,
            ephemeral.FormalArgumentConstraint: lambda node, context: node.type,
        }
    
    def infer(self, expression, context):
        expression_type = self._inferers[type(expression)](expression, context)
        self._type_lookup[expression] = expression_type
        return expression_type
    
    def _infer_none(self, node, context):
        return types.none_type
    
    def _infer_bool(self, node, context):
        return types.boolean_type
    
    def _infer_int(self, node, context):
        return types.int_type

    def _infer_str(self, node, context):
        return types.str_type
    
    def _infer_tuple_literal(self, node, context):
        element_types = [self.infer(element, context) for element in node.elements]
        return types.tuple(*element_types)
    
    def _infer_list_literal(self, node, context):
        element_types = [self.infer(element, context) for element in node.elements]
        return types.list_type(types.unify(element_types))

    def _infer_dict_literal(self, node, context):
        key_types = [self.infer(key, context) for key, value in node.items]
        value_types = [self.infer(value, context) for key, value in node.items]
        return types.dict_type(types.unify(key_types), types.unify(value_types))

    def _infer_ref(self, node, context):
        return context.lookup(node)

    def _infer_call(self, node, context):
        callee_type = self.infer(node.func, context)
        return self._infer_call_with_callee_type(node, callee_type, context)
    
    def _infer_call_with_callee_type(self, node, callee_type, context):
        def read_actual_arg(actual_arg, index):
            if isinstance(actual_arg, ephemeral.FormalArgumentConstraint) and actual_arg.formal_arg_node is None:
                return ephemeral.formal_arg_constraint(ephemeral.formal_arg(node.func, index), actual_arg.type)
            else:
                return actual_arg
        
        if types.is_overloaded_func_type(callee_type):
            # TODO: this still allows some ambiguity e.g. if a function is
            # overloaded with types "int -> int" and "v: int -> str", then
            # the call f(v=1) is still potentially ambiguous since it *may*
            # match the first type
            # It's also ambiguous due to sub-classing e.g. if a function is
            # overloaded with types "A -> int" and "B -> str", then passing
            # in an instance of "B" may in fact result in "int" being returned
            # since that instance was *also* a subclass of "B".
            # Since we have the restriction that many built-ins (e.g. int) can't be
            # sub-classed, perhaps we check for ambiguities by passing in the bottom
            # type as the arg type instead of any non-primitive?
            _possible_return_types = []
            # TODO: remove internal access
            for type_ in callee_type._types:
                try:
                    _possible_return_types.append(self._infer_call_with_callee_type(node, type_, context))
                except errors.TypeCheckError:
                    pass
            if len(_possible_return_types) > 0:
                return types.unify(_possible_return_types)
            else:
                # TODO: more descriptive error
                raise errors.ArgumentsError(node, "could not find matching overload")
                
        call_function_type = self._get_call_type(node.func, callee_type)
        
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

    def _get_call_type(self, node, callee_type):
        if types.is_func_type(callee_type):
            return callee_type
        elif "__call__" in callee_type.attrs:
            return self._get_call_type(node, callee_type.attrs.type_of("__call__"))
        else:
            raise errors.UnexpectedValueTypeError(node, expected="callable object", actual=callee_type)


    def _infer_attr(self, node, context):
        value_type = self.infer(node.value, context)
        if node.attr in value_type.attrs:
            return value_type.attrs.type_of(node.attr)
        else:
            raise errors.NoSuchAttributeError(node, str(value_type), node.attr)


    def _infer_type_application(self, node, context):
        generic_type = self.infer_type_value(node.generic_type, context)
        type_params = [
            self.infer_type_value(param, context)
            for param in node.params
        ]
        return generic_type(*type_params)
    
    def infer_type_value(self, node, context):
        meta_type = self.infer(node, context)
        if not types.is_meta_type(meta_type):
            raise errors.UnexpectedValueTypeError(node,
                expected="type",
                actual=meta_type,
            )
        return meta_type.type
        

    def _infer_binary_operation(self, node, context):
        if node.operator in ["bool_and", "bool_or"]:
            return types.unify([
                self.infer(node.left, context),
                self.infer(node.right, context),
            ])
        elif node.operator == "is":
            self.infer(node.left, context)
            self.infer(node.right, context)
            return types.boolean_type
        else:
            return self.infer_magic_method_call(node, node.operator, node.left, [node.right], context)
    
    def _infer_unary_operation(self, node, context):
        if node.operator == "bool_not":
            self.infer(node.operand, context)
            return types.boolean_type
        else:
            return self.infer_magic_method_call(node, node.operator, node.operand, [], context)
    
    def _infer_subscript(self, node, context):
        return self.infer_magic_method_call(node, "getitem", node.value, [node.slice], context)
    
    
    def _infer_slice(self, node, context):
        return types.slice_type(
            self.infer(node.start, context),
            self.infer(node.stop, context),
            self.infer(node.step, context),
        )
    
    def _infer_list_comprehension(self, node, context):
        self._infer_comprehension(node.generator, context)
        element_type = self.infer(node.element, context)
        return types.list_type(element_type)
    
    def _infer_generator_expression(self, node, context):
        self._infer_comprehension(node.generator, context)
        element_type = self.infer(node.element, context)
        return types.iterator(element_type)
    
    def _infer_comprehension(self, node, context):
        element_type = self.infer_iterable_element_type(node.iterable, context)
        assignment = Assignment(self)
        assignment.assign(node, node.target, element_type, context)
    
    def infer_magic_method_call(self, node, short_name, receiver, actual_args, context):
        method_name = "__{}__".format(short_name)
        
        call_node = ephemeral.call(
            node,
            ephemeral.attr(receiver, method_name),
            actual_args,
        )
        return self._infer_call(call_node, context)
    
    def _type_check_args(self, node, actual_args, formal_arg_types, context):
        for actual_arg, formal_arg_type in zip(actual_args, formal_arg_types):
            actual_arg_type = self.infer(actual_arg, context)
            if not types.is_sub_type(formal_arg_type, actual_arg_type):
                if isinstance(actual_arg, ephemeral.FormalArgumentConstraint):
                    raise errors.UnexpectedTargetTypeError(
                        actual_arg.formal_arg_node,
                        value_type=actual_arg_type,
                        target_type=formal_arg_type
                    )
                else:
                    raise errors.UnexpectedValueTypeError(
                        actual_arg,
                        expected=formal_arg_type,
                        actual=actual_arg_type
                    )
    
    
    def infer_iterable_element_type(self, node, context):
        iterable_type = self.infer(node, context)
        if "__iter__" in iterable_type.attrs:
            iterator_type = self.infer_magic_method_call(node, "iter", node, [], context)
            if not types.iterator.is_instantiated_type(iterator_type):
                raise errors.BadSignatureError(node, "__iter__ should return an iterator")
            
            element_type, = iterator_type.params
            return element_type
        elif "__getitem__" in iterable_type.attrs:
            args = [ephemeral.formal_arg_constraint(types.int_type)]
            return self.infer_magic_method_call(node, "getitem", node, args, context)
        else:
            raise errors.UnexpectedValueTypeError(node, expected="iterable type", actual=iterable_type)


_ordinal_suffixes = {1: "st", 2: "nd", 3: "rd"}

def _ordinal(num):
    if 10 <= num % 100 <= 20:
        suffix = "th"
    else:
        suffix = _ordinal_suffixes.get(num % 10, "th")
    
    return "{}{}".format(num, suffix)
