import zuice

from . import builtins, name_resolution, visit, nodes
from .parser.typing import TypeComments


ModuleName = zuice.key("ModuleName")
FuncName = zuice.key("FuncName")

class ClassBuilderTransform(zuice.Base):
    _name_resolver = zuice.dependency(name_resolution.NameResolver)
    _module_name = zuice.dependency(ModuleName)
    _func_name = zuice.dependency(FuncName)
    
    def __call__(self, module_node):
        references = self._name_resolver.resolve(module_node)
        
        visitor = visit.Visitor(visit_explicit_types=True)
        visitor.replace(nodes.Assignment, self._assignment)
        return visitor.visit(module_node, references)


    def _assignment(self, visitor, node, references):
        # TODO: handle cases that are currently asserted not to be true
        
        if not isinstance(node.value, nodes.Call):
            return node
        
        call = node.value
        callee = call.func
        
        if not isinstance(callee, nodes.AttributeAccess):
            return node
        
        if not isinstance(callee.value, nodes.VariableReference):
            return node
        
        if not references.referenced_declaration(callee.value) != builtins.builtin_modules[self._module_name]:
            return node
        
        if callee.attr != self._func_name:
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
            if not isinstance(attribute_node, nodes.FieldDefinition):
                raise Exception("fields of {}.{} must be declared as a field using :field".format(self._module_name, self._func_name))
            
            name_node = attribute_node.name
            assert isinstance(name_node, nodes.StringLiteral)
            return name_node.value, attribute_node.type
        
        attributes = list(map(_read_attribute, attribute_list.elements))
        
        init = nodes.func(
            "__init__",
            args=nodes.arguments(
                [nodes.argument("self")] +
                    [nodes.argument(name) for name, _ in attributes]
            ),
            body=[
                nodes.assign([nodes.attr(nodes.ref("self"), name)], nodes.ref(name))
                for name, _ in attributes
            ],
            explicit_type=nodes.signature(
                args=[nodes.signature_arg(nodes.ref("Self"))] +
                    [nodes.signature_arg(attr_type) for _, attr_type in attributes],
                # TODO: have a way to always reference the builtin none
                returns=nodes.ref("none")
            ),
        )
        
        return nodes.class_(
            name=name.value,
            body=[
                init
            ]
        )
        
