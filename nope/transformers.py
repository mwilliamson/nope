import zuice
import dodge

from . import builtins, name_resolution, nodes


ModuleName = zuice.key("ModuleName")
FuncName = zuice.key("FuncName")

class ClassBuilderTransform(zuice.Base):
    _name_resolver = zuice.dependency(name_resolution.NameResolver)
    _module_name = zuice.dependency(ModuleName)
    _func_name = zuice.dependency(FuncName)
    
    def __call__(self, module_node):
        references = self._name_resolver.resolve(module_node)
        
        return self._transform(module_node, references)
    
    def _transform(self, node, references):
        if self._is_class_builder_assignment(node, references):
            return self._transform_assignment(node, references)
        else:
            return self._map_nodes(node, references)
    
    def _is_class_builder_assignment(self, node, references):
        if not isinstance(node, nodes.Assignment):
            return False
        
        if not isinstance(node.value, nodes.Call):
            return False
        
        call = node.value
        callee = call.func
        
        if not isinstance(callee, nodes.AttributeAccess):
            return False
        
        if not isinstance(callee.value, nodes.VariableReference):
            return False
        
        if not references.referenced_declaration(callee.value) != builtins.builtin_modules[self._module_name]:
            return False
        
        if callee.attr != self._func_name:
            return False
        
        return True

    def _transform_assignment(self, node, references):
        call = node.value
        callee = call.func
        
        # TODO: handle cases that are currently asserted not to be true
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
            type=nodes.signature(
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
        
    def _map_nodes(self, node, references):
        fields = [
            self._transform_field(getattr(node, field.name), references)
            for field in dodge.fields(node)
        ]
        
        new_node = type(node)(*fields)
        # TODO: test location preservation
        location = getattr(node, "location", None)
        if location is not None:
            new_node.location = location
        
        return new_node
    
    def _transform_field(self, field, references):
        if isinstance(field, tuple):
            return tuple(self._transform_field(element, references) for element in field)
        if isinstance(field, list):
            return [self._transform_field(element, references) for element in field]
        elif isinstance(field, dict):
            return dict(
                (key, self._transform_field(value, references))
                for key, value in field.items()
            )
        elif isinstance(field, (type(None), bool, int, str)):
            return field
        else:
            return self._transform(field, references)
