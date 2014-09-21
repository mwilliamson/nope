from .. import nodes, types, errors
from . import ephemeral


class Assignment(object):
    def __init__(self, expression_type_inferer, on_ref=None):
        self._expression_type_inferer = expression_type_inferer
        self._on_ref = on_ref
    
    
    def assign(self, node, target, value_type, context):
        if isinstance(target, nodes.VariableReference):
            self._assign_ref(node, target, value_type, context)
        elif isinstance(target, nodes.AttributeAccess):
            self._assign_attr(node, target, value_type, context)
        elif isinstance(target, nodes.Subscript):
            self._assign_subscript(node, target, value_type, context)
        elif isinstance(target, nodes.TupleLiteral):
            self._assign_tuple_literal(node, target, value_type, context)
        else:
            raise Exception("Not implemented yet")
    
    
    def _assign_ref(self, node, target, value_type, context):
        var_type = context.lookup(target, allow_unbound=True)
        if var_type is not None and not types.is_sub_type(var_type, value_type):
            raise errors.UnexpectedTargetTypeError(node, target_type=var_type, value_type=value_type)
        
        # TODO: add test demonstrating necessity of `if var_type is None`
        if var_type is None:
            context.update_type(target, value_type)
        
        if self._on_ref is not None:
            self._on_ref(target, value_type, context)


    def _assign_attr(self, node, target, value_type, context):
        target_type = self._infer(target, context)
        
        if not types.is_sub_type(target_type, value_type):
            raise errors.UnexpectedTargetTypeError(target, value_type=value_type, target_type=target_type)
        
        obj_type = self._infer(target.value, context)
        if obj_type.attrs.get(target.attr).read_only:
            raise errors.ReadOnlyAttributeError(target, obj_type, target.attr)
    
    def _assign_subscript(self, node, target, value_type, context):
        self._expression_type_inferer.infer_magic_method_call(
            node,
            "setitem",
            target.value,
            [target.slice, ephemeral.formal_arg_constraint(value_type)],
            context,
        )
    
    def _assign_tuple_literal(self, node, target, value_type, context):
        if len(target.elements) != len(value_type.params):
            raise errors.UnpackError(target, len(target.elements), len(value_type.params))
        
        for element, element_type in zip(target.elements, value_type.params):
            self.assign(node, element, element_type, context)
        
    def _infer(self, node, context):
        return self._expression_type_inferer.infer(node, context)
