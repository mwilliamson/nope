from nose.tools import istest, assert_equal

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
        
