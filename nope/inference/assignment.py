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
        context.update_type(target, value_type)
        
        if self._on_ref is not None:
            self._on_ref(target, value_type, context)


    def _assign_attr(self, node, target, value_type, context):
        target_type = self._infer(target, context)
        obj_type = self._infer(target.value, context)
        
        if types.is_unknown(target_type):
            obj_type.attrs.get(target.attr).type = value_type
        elif not types.is_sub_type(target_type, value_type):
            raise errors.UnexpectedTargetTypeError(target, value_type=value_type, target_type=target_type)
        
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
        if not types.is_tuple(value_type):
            raise errors.CanOnlyUnpackTuplesError(target)
            
        if len(target.elements) != len(value_type.type_params):
            raise errors.UnpackError(target, len(target.elements), len(value_type.type_params))
        
        for element, element_type in zip(target.elements, value_type.type_params):
            self.assign(node, element, element_type, context)
        
    def _infer(self, node, context):
        return self._expression_type_inferer.infer(node, context)
