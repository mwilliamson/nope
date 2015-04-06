from .. import nodes, types, errors
from . import ephemeral
from .assignment import Assignment


class ExpressionTypeInferer(object):
    def __init__(self, type_lookup):
        self._type_lookup = type_lookup
        
        self._inferers = {
            nodes.NoneLiteral: self._infer_none,
            nodes.BooleanLiteral: self._infer_bool,
            nodes.IntLiteral: self._infer_int,
            nodes.StringLiteral: self._infer_str,
            nodes.TupleLiteral: self._infer_tuple_literal,
            nodes.ListLiteral: self._infer_list_literal,
            nodes.DictLiteral: self._infer_dict_literal,
            nodes.VariableReference: self._infer_ref,
            nodes.Call: self._infer_call,
            nodes.AttributeAccess: self._infer_attr,
            nodes.TypeApplication: self._infer_type_application,
            nodes.TypeUnion: self._infer_type_union,
            nodes.FunctionSignature: self._infer_function_signature,
            nodes.BinaryOperation: self._infer_binary_operation,
            nodes.UnaryOperation: self._infer_unary_operation,
            nodes.Subscript: self._infer_subscript,
            nodes.Slice: self._infer_slice,
            nodes.Comprehension: self._infer_comprehension,
            ephemeral.FormalArgumentConstraint: lambda node, context, hint: node.type,
        }
    
    def infer(self, expression, context, hint=None, required_type=None):
        expression_type = self._inferers[type(expression)](expression, context, required_type or hint)
        
        if required_type is not None and not types.is_sub_type(required_type, expression_type):
            raise errors.UnexpectedValueTypeError(expression,
                expected=required_type,
                actual=expression_type)
        
        self._type_lookup[expression] = expression_type
        return expression_type
    
    def _infer_none(self, node, context, hint):
        return types.none_type
    
    def _infer_bool(self, node, context, hint):
        return types.bool_type
    
    def _infer_int(self, node, context, hint):
        return types.int_type

    def _infer_str(self, node, context, hint):
        return types.str_type
    
    def _infer_tuple_literal(self, node, context, hint):
        element_types = [self.infer(element, context) for element in node.elements]
        return types.tuple_type(*element_types)
    
    def _infer_list_literal(self, node, context, hint):
        element_types = [self.infer(element, context) for element in node.elements]
        common_super_type = types.common_super_type(element_types)
        
        if hint is not None and types.list_type.is_instantiated_type(hint) and types.is_sub_type(hint.type_params[0], common_super_type):
            return hint
        else:
            return types.list_type(common_super_type)

    def _infer_dict_literal(self, node, context, hint):
        key_types = [self.infer(key, context) for key, value in node.items]
        value_types = [self.infer(value, context) for key, value in node.items]
        
        key_super_type = types.common_super_type(key_types)
        value_super_type = types.common_super_type(value_types)
        
        hint_is_valid = (
            hint is not None and
            types.dict_type.is_instantiated_type(hint) and
            types.is_sub_type(hint.type_params[0], key_super_type) and
            types.is_sub_type(hint.type_params[1], value_super_type)
        )
        
        if hint_is_valid:
            return hint
        else:
            return types.dict_type(key_super_type, value_super_type)

    def _infer_ref(self, node, context, hint):
        return context.lookup(node)

    def _infer_call(self, node, context, hint):
        callee_type = self.infer(node.func, context)
        for arg in node.args:
            self.infer(arg, context)
        for arg in node.kwargs.values():
            self.infer(arg, context)
            
        return self._infer_call_with_callee_type(node, callee_type, context)
    
    def _infer_call_with_callee_type(self, node, callee_type, context):
        if types.is_overloaded_func_type(callee_type):
            return self._infer_overloaded_func_call(node, callee_type, context)
                
        type_params, call_function_type = self._get_call_type(node.func, callee_type)

        formal_arg_types = [
            arg.type
            for arg in call_function_type.args
        ]
                    
        actual_args = self._generate_actual_args(node, call_function_type.args)
        actual_arg_types = [
            self.infer(actual_arg, context, hint=formal_arg_type)
            for actual_arg, formal_arg_type in zip(actual_args, formal_arg_types)
        ]
        
        if type_params:
            actual_func_type = types.func(actual_arg_types, types.object_type)
            # TODO: unify these two ways of checking args -- the logic is effectively
            # duplicated in this class and in types.is_sub_type, and the user gets
            # less informative errors in the generic case
            type_map = types.is_sub_type(actual_func_type, call_function_type, unify=type_params)
            if type_map is None:
                message = "cannot call function of type: {}\nwith arguments: {}".format(
                    call_function_type, ", ".join(map(str, actual_func_type.args)))
                raise errors.ArgumentsError(node, message)
            return call_function_type.instantiate_with_type_map(type_map).return_type
        else:
            self._type_check_args(
                node,
                list(zip(actual_args, actual_arg_types)),
                type_params,
                formal_arg_types,
                context
            )
            return call_function_type.return_type

    def _get_call_type(self, node, callee_type):
        if types.is_func_type(callee_type):
            return [], callee_type
        elif types.is_generic_func(callee_type):
            return callee_type.formal_type_params, callee_type
        elif "__call__" in callee_type.attrs:
            return self._get_call_type(node, callee_type.attrs.type_of("__call__"))
        else:
            raise errors.UnexpectedValueTypeError(node, expected="callable object", actual=callee_type)
    
    
    def _infer_overloaded_func_call(self, node, callee_type, context):
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
            return types.common_super_type(_possible_return_types)
        else:
            # TODO: more descriptive error
            raise errors.ArgumentsError(node, "could not find matching overload")
    
    
    def _generate_actual_args(self, node, formal_args):
        if len(node.args) > len(formal_args):
            raise errors.ArgumentsError(
                node,
                "function takes {} positional arguments but {} was given".format(
                    len(formal_args),
                    len(node.args))
            )
            
        def read_actual_arg(actual_arg, index):
            if isinstance(actual_arg, ephemeral.FormalArgumentConstraint) and actual_arg.formal_arg_node is None:
                return ephemeral.formal_arg_constraint(ephemeral.formal_arg(node.func, index), actual_arg.type)
            else:
                return actual_arg
        
        kwarg_nodes = node.kwargs.copy()
        actual_args = []
        
        for index, formal_arg in enumerate(formal_args):
            formal_arg_name = formal_arg.name
            positional_arg = None
            keyword_arg = None
            
            if index < len(node.args):
                positional_arg = node.args[index]
            if formal_arg_name is not None:
                keyword_arg = kwarg_nodes.pop(formal_arg_name, None)
            
            if positional_arg is not None and keyword_arg is not None:
                raise errors.ArgumentsError(node, "multiple values for argument '{}'".format(formal_arg_name))
            elif positional_arg is not None:
                actual_args.append(read_actual_arg(positional_arg, index))
            elif keyword_arg is not None:
                actual_args.append(read_actual_arg(keyword_arg, index))
            elif not formal_arg.optional:
                if formal_arg_name is None:
                    message = "missing {} positional argument".format(_ordinal(index + 1))
                else:
                    message = "missing argument '{}'".format(formal_arg_name)
                raise errors.ArgumentsError(node, message)
        
        if kwarg_nodes:
            first_key = next(iter(kwarg_nodes.keys()))
            raise errors.ArgumentsError(node, "unexpected keyword argument '{}'".format(first_key))
        
        return actual_args
    

    def _infer_attr(self, node, context, hint):
        value_type = self.infer(node.value, context)
        if node.attr in value_type.attrs:
            return value_type.attrs.type_of(node.attr)
        else:
            raise errors.NoSuchAttributeError(node, str(value_type), node.attr)


    def _infer_type_application(self, node, context, hint):
        generic_type = self.infer_type_value(node.generic_type, context)
        type_params = [
            self.infer_type_value(param, context)
            for param in node.params
        ]
        return types.meta_type(generic_type(*type_params))
    
    def _infer_type_union(self, node, context, hint):
        constituent_types = [
            self.infer_type_value(type_node, context)
            for type_node in node.types
        ]
        return types.meta_type(types.union(*constituent_types))
    
    def _infer_function_signature(self, node, context, hint):
        formal_type_params = [
            types.invariant(type_param_node.name)
            for type_param_node in node.type_params
        ]
        
        if formal_type_params:
            def inner_func_type(*actual_type_params):
                # TODO: remove duplication with generic classes
                inner_context = context.enter_statement()
                for type_param_node, type_param in zip(node.type_params, actual_type_params):
                    inner_context.update_type(type_param_node, types.meta_type(type_param))
                
                return self._infer_inner_function_signature(node, inner_context)
                
            
            func_type = types.generic_func(formal_type_params, inner_func_type)
        else:
            func_type = self._infer_inner_function_signature(node, context)
        return types.meta_type(func_type)
    
    def _infer_inner_function_signature(self, node, context):
        args = [self._read_signature_arg(arg, context) for arg in node.args]
        return_type = self.infer_type_value(node.returns, context)
        
        return types.func(args, return_type)
    
    def _read_signature_arg(self, arg, context):
        return types.func_arg(
            arg.name,
            self.infer_type_value(arg.type, context),
            optional=arg.optional,
        )
    
    def infer_type_value(self, node, context):
        meta_type = self.infer(node, context)
        if not types.is_meta_type(meta_type):
            raise errors.UnexpectedValueTypeError(node,
                expected="type",
                actual=meta_type,
            )
        return meta_type.type
        

    def _infer_binary_operation(self, node, context, hint):
        if node.operator in ["bool_and", "bool_or"]:
            return types.common_super_type([
                self.infer(node.left, context),
                self.infer(node.right, context),
            ])
        elif node.operator in ["is", "is_not"]:
            self.infer(node.left, context)
            self.infer(node.right, context)
            return types.bool_type
        else:
            return self.infer_magic_method_call(node, node.operator, node.left, [node.right], context)
    
    def _infer_unary_operation(self, node, context, hint):
        if node.operator == "bool_not":
            self.infer(node.operand, context)
            return types.bool_type
        else:
            return self.infer_magic_method_call(node, node.operator, node.operand, [], context)
    
    def _infer_subscript(self, node, context, hint):
        return self.infer_magic_method_call(node, "getitem", node.value, [node.slice], context)
    
    
    def _infer_slice(self, node, context, hint):
        return types.slice_type(
            self.infer(node.start, context),
            self.infer(node.stop, context),
            self.infer(node.step, context),
        )
    
    def _infer_comprehension(self, node, context, hint):
        iterable_element_type = self.infer_iterable_element_type(node.iterable, context)
        assignment = Assignment(self)
        assignment.assign(node, node.target, iterable_element_type, context)
        comprehension_element_type = self.infer(node.element, context)
        return self._generate_comprehension_type(node.comprehension_type, comprehension_element_type)
    
    def _generate_comprehension_type(self, comprehension_type, element_type):
        return {
            "list_comprehension": types.list_type,
            "generator_expression": types.iterator,
        }[comprehension_type](element_type)
    
    def infer_magic_method_call(self, node, short_name, receiver, actual_args, context):
        method_name = "__{}__".format(short_name)
        
        call_node = ephemeral.call(
            node,
            ephemeral.attr(receiver, method_name),
            actual_args,
        )
        return self._infer_call(call_node, context, hint=None)
    
    def _type_check_args(self, node, actual_args, type_params, formal_arg_types, context):
        for (actual_arg, actual_arg_type), formal_arg_type in zip(actual_args, formal_arg_types):
            # TODO: need to ensure unified type params are consistent
            if not types.is_sub_type(formal_arg_type, actual_arg_type, unify=type_params):
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
            if not types.is_instantiated_sub_type(types.iterator, iterator_type):
                raise errors.BadSignatureError(node, "__iter__ should return an iterator")
            
            element_type, = iterator_type.type_params
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
