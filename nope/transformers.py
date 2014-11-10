import zuice

from . import builtins, name_resolution, visit, nodes


class CollectionsNamedTupleTransform(zuice.Base):
    _name_resolver = zuice.dependency(name_resolution.NameResolver)
    
    def __call__(self, module_node):
        references = self._name_resolver.resolve(module_node)
        
        visitor = visit.Visitor(visit_explicit_types=True)
        visitor.replace(nodes.Assignment, _assignment)
        return visitor.visit(module_node, references)


def _assignment(visitor, node, references):
    # TODO: handle cases that are currently asserted not to be true
    
    if not isinstance(node.value, nodes.Call):
        return node
    
    call = node.value
    callee = call.func
    
    if not isinstance(callee, nodes.AttributeAccess):
        return node
    
    if not isinstance(callee.value, nodes.VariableReference):
        return node
    
    if not references.referenced_declaration(callee.value) != builtins.builtin_modules["collections"]:
        return node
    
    if callee.attr != "namedtuple":
        return node
    
    assert len(node.targets) == 1
    target, = node.targets
    assert isinstance(target, nodes.VariableReference)
    
    assert len(call.args) == 2
    name, attribute_list = call.args
    
    assert isinstance(name, nodes.StringLiteral)
    assert name.value == target.name
    assert isinstance(attribute_list, nodes.ListLiteral)
    
    def _read_attribute(attribute_node):
        assert isinstance(attribute_node, nodes.StringLiteral)
        explicit_type = nodes.explicit_type_of(attribute_node)
        if explicit_type is None:
            raise Exception("fields of collections.namedtuple must have explicit type")
        return attribute_node.value, explicit_type
    
    attributes = list(map(_read_attribute, attribute_list.elements))
    
    init = nodes.typed(
        nodes.signature(
            args=[nodes.signature_arg(nodes.ref("Self"))] +
                [nodes.signature_arg(attr_type) for _, attr_type in attributes],
            # TODO: have a way to always reference the builtin none
            returns=nodes.ref("none")
        ),
        nodes.func(
            "__init__",
            nodes.arguments(
                [nodes.argument("self")] +
                    [nodes.argument(name) for name, _ in attributes]
            ),
            [
                nodes.assign([nodes.attr(nodes.ref("self"), name)], nodes.ref(name))
                for name, _ in attributes
            ],
        )
    )
    
    return nodes.class_def(
        name=name.value,
        body=[
            init
        ]
    )
    
