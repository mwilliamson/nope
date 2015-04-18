from .. import nodes, types, errors, structure
from ..lists import filter_by_type


class ClassDefinitionTypeChecker(object):
    def __init__(self, statement_type_checker, declaration_finder, expression_type_inferer):
        self._statement_type_checker = statement_type_checker
        self._update_context = statement_type_checker.update_context
        self._infer_function_def = statement_type_checker.infer_function_def
        self._declaration_finder = declaration_finder
        self._expression_type_inferer = expression_type_inferer
    
    def check_class_definition(self, node, context):
        self._check_base_classes(node, context)
        self._check_class_assignments(node, context)
        inner_meta_type = self._infer_class_type(node, context)
        self._check_class_methods(node, context, inner_meta_type)
    
    def _check_base_classes(self, node, context):
        base_classes = [
            self._infer_type_value(base_class, context)
            for base_class in node.base_classes
        ]
        if any(base_class != types.object_type for base_class in base_classes):
            raise errors.UnsupportedError("base classes other than 'object' are not supported")
    
    def _check_class_assignments(self, node, context):
        assignments = filter_by_type(nodes.Assignment, node.body)
        for assignment in assignments:
            self._update_context(assignment, context)
        
    def _infer_class_type(self, node, context):
        if node.type_params:
            formal_type_params = [
                types.invariant(type_param_node.name)
                for type_param_node in node.type_params
            ]
            
            def instantiate(name, *actual_type_params):
                return types.class_type(name)
            
            def instantiate_attrs(inner_class_type, *actual_type_params):
                # TODO: make context immutable.
                # Variables can change type over time (which we should probably
                # disallow entirely if they're captured by a function/class, or do something clever with SSA).
                # Also, we explicitly change the type of the type parameters each time we instantiate.
                # This should be fine since we don't interleave instantiations, but it feels messy (read: bug-prone).
                # TODO: rename enter_statement (or create alias) -- we're really just exploiting
                # the fact that this has a separate set of bindings from declaration to type
                inner_context = context.enter_statement()
                for type_param_node, type_param in zip(node.type_params, actual_type_params):
                    inner_context.update_type(type_param_node, types.meta_type(type_param))
                
                inner_meta_type = types.meta_type(inner_class_type)
                body_context = self._enter_class_body_context(node, inner_context, inner_meta_type)
                self._add_attrs_to_inner_type(node, body_context, inner_meta_type)
            
            for type_param_node, type_param in zip(node.type_params, formal_type_params):
                context.update_type(type_param_node, types.meta_type(type_param))
                
            class_type = types.generic(node.name, formal_type_params, instantiate, complete_type=instantiate_attrs)
            meta_type = types.meta_type(class_type)
            context.update_type(node, meta_type)
            
            def inner_constructor_type(*actual_type_params):
                inner_class_type = class_type(*actual_type_params)
                return self._constructor_type(inner_class_type)
                
            constructor_type = types.generic_func(
                formal_type_params,
                inner_constructor_type
            )
            meta_type.attrs.add("__call__", constructor_type, read_only=True)
            return types.meta_type(class_type.instantiate(formal_type_params))
        else:
            class_type = types.class_type(node.name)
            meta_type = types.meta_type(class_type)
            
            context.update_type(node, meta_type)
            
            body_context = self._enter_class_body_context(node, context, meta_type)
            
            self._add_attrs_to_inner_type(node, body_context, meta_type)
            
            constructor_type = self._constructor_type(class_type)
            meta_type.attrs.add("__call__", constructor_type, read_only=True)
            
            return meta_type
    
    def _add_attrs_to_inner_type(self, node, body_context, inner_meta_type):
        inner_class_type = inner_meta_type.type
        
        attr_types = self._unbound_attribute_types(node, body_context)
        
        for method_name, (method_node, func_type) in attr_types.items():
            self._add_attr_to_type(method_node, inner_meta_type, method_name, func_type)
            
        init = attr_types.get("__init__")
        
        if init is not None:
            init_node, init_func_type = init
            self._check_init_statements(init_node, body_context, inner_class_type)
            
            self._update_context(init_node, body_context, immediate=True)
    
    def _unbound_attribute_types(self, node, body_context):
        attrs = self._unbound_assigned_attribute_types(node, body_context)
        attrs.update(self._unbound_method_types(node, body_context))
        return attrs
    
    def _unbound_assigned_attribute_types(self, node, context):
        attrs = dict(
            (target.name, (assignment, context.lookup(target)))
            for assignment in filter_by_type(nodes.Assignment, node.body)
            for target in assignment.targets
            if isinstance(target, nodes.VariableReference)
        )
        
        init = attrs.get("__init__")
        if init is not None:
            raise errors.InitAttributeMustBeFunctionDefinitionError(init[0])
        
        return attrs
    
    def _unbound_method_types(self, node, body_context):
        return dict(
            (method_node.name, (method_node, self._infer_function_def(method_node, body_context)))
            for method_node in filter_by_type(nodes.FunctionDef, node.body)
        )
    
    def _constructor_type(self, class_type):
        init_type = class_type.attrs.type_of("__init__")
        if init_type is None:
            return types.func([], class_type)
        else:
            return types.func(init_type.args, class_type)
    
    def _check_class_methods(self, node, context, meta_type):
        body_context = self._enter_class_body_context(node, context, meta_type)
        
        for function_definition in filter_by_type(nodes.FunctionDef, node.body):
            self._update_context(function_definition, body_context)
        
    
    def _add_attr_to_type(self, node, meta_type, attr_name, attr_type):
        class_type = meta_type.type
        is_init_method = attr_name == "__init__"
        
        if types.is_func_type(attr_type):
            self._check_method_receiver_argument(node, class_type, attr_name, attr_type)
            method_type = self._function_type_to_method_type(attr_type)
            if is_init_method and method_type.return_type != types.none_type:
                raise errors.InitMethodsMustReturnNoneError(node)
            # TODO: ideally, __init__ wouldn't be present as an attr
            class_type.attrs.add(attr_name, method_type)
        else:
            class_type.attrs.add(attr_name, attr_type)
            meta_type.attrs.add(attr_name, attr_type)
    
    
    def _enter_class_body_context(self, node, context, meta_type):
        body_context = context.enter_class()
        class_declarations = self._declaration_finder.declarations_in(node)
        body_context.update_declaration_type(
            class_declarations.declaration("Self"),
            meta_type
        )
        return body_context
        
    
    def _check_init_statements(self, node, context, class_type):
        declarations_in_function = self._declaration_finder.declarations_in(node)
        self_arg_name = node.args.args[0].name
        self_declaration = declarations_in_function.declaration(self_arg_name)
        
        def is_self(ref):
            return context.referenced_declaration(ref) == self_declaration
            
        for statement in node.body:
            self._check_init_statement(
                statement=statement,
                class_type=class_type,
                is_self=is_self)
    
    def _check_init_statement(self, statement, class_type, is_self):
        self_targets = []
        
        if isinstance(statement, nodes.Assignment):
            for target in statement.targets:
                is_self_attr_assignment = (
                    isinstance(target, nodes.AttributeAccess) and
                    is_self(target.value)
                )
                if is_self_attr_assignment:
                    class_type.attrs.add(target.attr, types.unknown_type, read_only=False)
                    self_targets.append(target.value)
        
        for descendant in structure.descendants(statement):
            if isinstance(descendant, nodes.VariableReference) and is_self(descendant) and descendant not in self_targets:
                raise errors.InitMethodCannotGetSelfAttributes(descendant)

    
    def _function_type_to_method_type(self, func_type):
        return types.func(func_type.args[1:], func_type.return_type)
    
    def _check_method_receiver_argument(self, class_node, class_type, attr_name, func_type):
        if len(func_type.args) < 1:
            raise errors.MethodHasNoArgumentsError(class_node, attr_name)
        
        formal_receiver_type = func_type.args[0].type
        if not types.is_sub_type(formal_receiver_type, class_type):
            raise errors.UnexpectedReceiverTypeError(
                class_node,
                receiver_type=formal_receiver_type,
            )
    
    def _infer_type_value(self, *args, **kwargs):
        return self._expression_type_inferer.infer_type_value(*args, **kwargs)
