from nose.tools import istest, assert_equal, assert_not_equal

from nope import types


_formal_param = types._FormalParameter("T")

@istest
class TypeSubstitutionTests(object):
    @istest
    def type_substitution_replaces_formal_parameters_with_value_set_in_type_map(self):
        replacement_type = types.ScalarType("Counter", {})
        new_type = types._substitute_types(_formal_param, {_formal_param: replacement_type})
        assert_equal(replacement_type, new_type)
    
    @istest
    def formal_type_parameter_is_unchanged_if_not_in_type_map(self):
        replacement_type = types.ScalarType("Counter", {})
        new_type = types._substitute_types(_formal_param, {types._FormalParameter("T"): replacement_type})
        assert_equal(_formal_param, new_type)
    
    @istest
    def dict_has_types_substituted_in_values(self):
        replacement_type = types.ScalarType("Counter", {})
        new_type = types._substitute_types({"x": _formal_param}, {_formal_param: replacement_type})
        assert_equal({"x": replacement_type}, new_type)
    
    @istest
    def scalar_type_is_unchanged_by_type_substitution(self):
        scalar_type = types.ScalarType("Blah", {"x": _formal_param})
        replacement_type = types.ScalarType("Counter", {})
        new_type = types._substitute_types(scalar_type, {_formal_param: replacement_type})
        assert_equal(scalar_type, new_type)
        

@istest
class TypeEqualityTests(object):
    @istest
    def scalar_type_is_equal_to_itself(self):
        scalar_type = types.ScalarType("Blah", {})
        assert_equal(scalar_type, scalar_type)
        
    @istest
    def scalar_type_is_not_equal_to_another_scalar_type_with_same_attributes(self):
        assert_not_equal(types.ScalarType("Blah", {}), types.ScalarType("Blah", {}))
        
    @istest
    def instantiated_type_is_not_equal_to_scalar_type(self):
        scalar_type = types.ScalarType("List", {})
        generic_type = types.generic_class("List", "T", {})
        instantiated_type = generic_type.instantiate([scalar_type])
        assert_not_equal(scalar_type, instantiated_type)
        
    @istest
    def instantiated_types_are_equal_if_they_have_the_same_substitutions_and_generic_type(self):
        scalar_type = types.ScalarType("Blah", {})
        generic_type = types.generic_class("List", "T", {})
        first_instantiated_type = generic_type.instantiate([scalar_type])
        second_instantiated_type = generic_type.instantiate([scalar_type])
        assert_equal(first_instantiated_type, second_instantiated_type)
        
    @istest
    def instantiated_types_are_not_equal_if_they_have_the_same_substitutions_but_different_generic_type(self):
        scalar_type = types.ScalarType("Blah", {})
        
        first_generic_type = types.generic_class("List", "T", {})
        second_generic_type = types.generic_class("List", "T", {})
        
        first_instantiated_type = first_generic_type.instantiate([scalar_type])
        second_instantiated_type = second_generic_type.instantiate([scalar_type])
        
        assert_not_equal(first_instantiated_type, second_instantiated_type)
        
    @istest
    def instantiated_types_are_not_equal_if_they_have_the_same_generic_type_but_different_substitutions(self):
        first_scalar_type = types.ScalarType("Blah", {})
        second_scalar_type = types.ScalarType("Blah", {})
        
        generic_type = types.generic_class("List", "T", {})
        
        first_instantiated_type = generic_type.instantiate([first_scalar_type])
        second_instantiated_type = generic_type.instantiate([second_scalar_type])
        
        assert_not_equal(first_instantiated_type, second_instantiated_type)


@istest
class SubTypeTests(object):
    @istest
    def scalar_type_is_subtype_of_itself(self):
        cls = types.ScalarType("Blah", {})
        assert types.is_sub_type(cls, cls)
        
    @istest
    def scalar_type_is_subtype_of_object_type(self):
        cls = types.ScalarType("Blah", {})
        assert types.is_sub_type(types.object_type, cls)
        
    @istest
    def scalar_type_is_subtype_of_base_class(self):
        super_type = types.ScalarType("Parent", {})
        cls = types.ScalarType("Blah", {}, base_classes=[super_type])
        assert types.is_sub_type(super_type, cls)
        assert not types.is_sub_type(cls, super_type)
        
    @istest
    def scalar_type_is_subtype_of_structural_type_if_it_has_subset_of_attrs(self):
        cls = types.ScalarType("Person", {
            "name": types.str_type,
            "number_of_hats": types.int_type,
        })
        structural_type = types.structural_type("HasName", {
            "name": types.str_type,
        })
        
        assert types.is_sub_type(structural_type, cls)
        assert not types.is_sub_type(cls, structural_type)
        
    @istest
    def scalar_type_is_not_subtype_of_structural_type_if_it_is_missing_attrs(self):
        cls = types.ScalarType("Person", {
        })
        structural_type = types.structural_type("HasName", {
            "name": types.str_type,
        })
        
        assert not types.is_sub_type(structural_type, cls)
        assert not types.is_sub_type(cls, structural_type)
