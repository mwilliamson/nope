from nose.tools import istest, assert_equal, assert_not_equal

from nope import types


_formal_param = types.invariant("T")
_scalar_type = types.scalar_type("User")
int_type = types.int_type
str_type = types.str_type
none_type = types.none_type


@istest
class TypeEqualityTests(object):
    @istest
    def scalar_type_is_equal_to_itself(self):
        scalar_type = types.scalar_type("Blah")
        assert_equal(scalar_type, scalar_type)
        
    @istest
    def scalar_type_is_not_equal_to_another_scalar_type_with_same_attributes(self):
        assert_not_equal(types.scalar_type("Blah"), types.scalar_type("Blah"))
        
    @istest
    def instantiated_type_is_not_equal_to_scalar_type(self):
        scalar_type = types.scalar_type("List")
        generic_type = types.generic_class("List", "T")
        instantiated_type = generic_type.instantiate([scalar_type])
        assert_not_equal(scalar_type, instantiated_type)
        
    @istest
    def instantiated_types_are_equal_if_they_have_the_same_substitutions_and_generic_type(self):
        scalar_type = types.scalar_type("Blah")
        generic_type = types.generic_class("List", "T")
        first_instantiated_type = generic_type.instantiate([scalar_type])
        second_instantiated_type = generic_type.instantiate([scalar_type])
        assert_equal(first_instantiated_type, second_instantiated_type)
        
    @istest
    def instantiated_types_are_not_equal_if_they_have_the_same_substitutions_but_different_generic_type(self):
        scalar_type = types.scalar_type("Blah")
        
        first_generic_type = types.generic_class("List", ["T"])
        second_generic_type = types.generic_class("List", ["T"])
        
        first_instantiated_type = first_generic_type.instantiate([scalar_type])
        second_instantiated_type = second_generic_type.instantiate([scalar_type])
        
        assert_not_equal(first_instantiated_type, second_instantiated_type)
        
    @istest
    def instantiated_types_are_not_equal_if_they_have_the_same_generic_type_but_different_substitutions(self):
        first_scalar_type = types.scalar_type("Blah")
        second_scalar_type = types.scalar_type("Blah")
        
        generic_type = types.generic_class("List", ["T"])
        
        first_instantiated_type = generic_type.instantiate([first_scalar_type])
        second_instantiated_type = generic_type.instantiate([second_scalar_type])
        
        assert_not_equal(first_instantiated_type, second_instantiated_type)


@istest
class SubTypeTests(object):
    @istest
    def scalar_type_is_subtype_of_itself(self):
        cls = types.scalar_type("Blah")
        assert types.is_sub_type(cls, cls)
        
    @istest
    def scalar_type_is_subtype_of_object_type(self):
        cls = types.scalar_type("Blah")
        assert types.is_sub_type(types.object_type, cls)
        
    @istest
    def scalar_type_is_subtype_of_base_class(self):
        super_type = types.scalar_type("Parent")
        cls = types.scalar_type("Blah", base_classes=[super_type])
        assert types.is_sub_type(super_type, cls)
        assert not types.is_sub_type(cls, super_type)
        
    @istest
    def scalar_type_is_subtype_of_base_class_of_base_class(self):
        super_super_type = types.scalar_type("GrandParent")
        super_type = types.scalar_type("Parent", base_classes=[super_super_type])
        cls = types.scalar_type("Blah", base_classes=[super_type])
        assert types.is_sub_type(super_super_type, cls)
        assert not types.is_sub_type(cls, super_super_type)
        
    @istest
    def scalar_type_is_subtype_of_structural_type_if_it_has_subset_of_attrs(self):
        # TODO: how to handle sub-typing of mutable attrs
        cls = types.scalar_type("Person", [
            types.attr("name", types.str_type),
            types.attr("number_of_hats", types.int_type),
        ])
        structural_type = types.structural_type("HasName", [
            types.attr("name", types.str_type),
        ])
        
        assert types.is_sub_type(structural_type, cls)
        assert not types.is_sub_type(cls, structural_type)
        
    @istest
    def scalar_type_is_not_subtype_of_structural_type_if_it_is_missing_attrs(self):
        cls = types.scalar_type("Person")
        structural_type = types.structural_type("HasName", [
            types.attr("name", types.str_type),
        ])
        
        assert not types.is_sub_type(structural_type, cls)
        assert not types.is_sub_type(cls, structural_type)
        
    @istest
    def scalar_type_is_subtype_of_structural_type_if_attr_is_subtype_of_attr_on_structural_type(self):
        cls = types.scalar_type("Person", [
            types.attr("name", types.str_type),
        ])
        structural_type = types.structural_type("HasName", [
            types.attr("name", types.object_type),
        ])
        
        assert types.is_sub_type(structural_type, cls)
        assert not types.is_sub_type(cls, structural_type)
        
    @istest
    def scalar_type_is_not_subtype_of_structural_type_if_attr_is_strict_supertype_of_attr_on_structural_type(self):
        cls = types.scalar_type("Person", [
            types.attr("name", types.object_type),
        ])
        structural_type = types.structural_type("HasName", [
            types.attr("name", types.str_type),
        ])
        
        assert not types.is_sub_type(structural_type, cls)
        assert not types.is_sub_type(cls, structural_type)
        
    @istest
    def rescursive_structural_types_do_not_cause_stack_overflow(self):
        recursive1 = types.structural_type("recursive1")
        recursive1.attrs.add("uh_oh", types.func([], recursive1))
        recursive2 = types.structural_type("recursive2")
        recursive2.attrs.add("uh_oh", types.func([], recursive2))
        
        assert not types.is_sub_type(
            recursive1,
            recursive2,
        )
        
    @istest
    def instantiated_generic_structural_type_is_sub_type_of_other_instantiated_generic_structural_type_if_it_has_matching_attributes(self):
        iterator = types.generic_structural_type("iterator", [types.covariant("T")], lambda T: [
            types.attr("__iter__", types.func([], iterator(T))),
            types.attr("__next__", types.func([], T)),
        ])

        iterable = types.generic_structural_type("iterable", [types.covariant("T")], lambda T: [
            types.attr("__iter__", types.func([], iterator(T))),
        ])
        
        assert types.is_sub_type(
            iterable(types.int_type),
            iterator(types.int_type),
        )
        
    @istest
    def recursive_instantiated_generic_structural_type_is_sub_type_of_same_instantiated_generic_structural_type_if_it_has_matching_attributes(self):
        recursive = types.generic_structural_type("recursive", [types.covariant("T")], lambda T: [
            types.attr("__iter__", types.func([], recursive(T))),
        ])
        
        assert types.is_sub_type(
            recursive(types.int_type),
            recursive(types.int_type),
        )
        
    @istest
    def type_is_subtype_of_union_type_if_it_appears_in_union_type(self):
        scalar_type = types.scalar_type("User")
        union_type = types.union(scalar_type, types.none_type)
        
        assert types.is_sub_type(union_type, scalar_type)
        assert not types.is_sub_type(scalar_type, union_type)
        
    @istest
    def union_type_is_subtype_of_other_union_type_if_its_types_are_a_subset(self):
        smaller_union_type = types.union(types.int_type, types.none_type)
        larger_union_type = types.union(types.int_type, types.none_type, types.str_type)
        
        assert types.is_sub_type(larger_union_type, smaller_union_type)
        assert not types.is_sub_type(smaller_union_type, larger_union_type)
        
    @istest
    def instantiated_union_type_is_subtype_of_other_instantiated_union_type_if_its_types_are_a_subset(self):
        smaller_union_type = types.generic(["T"], lambda T: types.union(T, types.none_type))
        larger_union_type = types.generic(["T"], lambda T: types.union(T, types.none_type, types.str_type))
        
        assert types.is_sub_type(larger_union_type(types.int_type), smaller_union_type(types.int_type))
        assert not types.is_sub_type(smaller_union_type(types.int_type), larger_union_type(types.int_type))
        
    @istest
    def union_of_union_is_treated_the_same_as_flat_union(self):
        nested_union_type = types.union(types.int_type, types.union(types.none_type, types.str_type))
        flat_union_type = types.union(types.int_type, types.none_type, types.str_type)
        
        assert types.is_sub_type(nested_union_type, flat_union_type)
        assert types.is_sub_type(flat_union_type, nested_union_type)
    
    @istest
    def instantiated_class_is_not_sub_type_of_other_instantiated_class_if_formal_param_is_invariant_and_type_params_are_different(self):
        generic_class = types.generic_class("iterator", [types.invariant("T")])
        
        assert not types.is_sub_type(generic_class(types.object_type), generic_class(types.int_type))
        assert not types.is_sub_type(generic_class(types.int_type), generic_class(types.object_type))
    
    @istest
    def instantiated_class_is_sub_type_of_other_instantiated_class_if_formal_param_is_covariant_and_type_params_are_subtypes(self):
        generic_class = types.generic_class("iterator", [types.covariant("T")])
        
        assert types.is_sub_type(generic_class(types.object_type), generic_class(types.int_type))
        assert not types.is_sub_type(generic_class(types.int_type), generic_class(types.object_type))
    
    @istest
    def instantiated_class_is_sub_type_of_other_instantiated_class_if_formal_param_is_contravariant_and_type_params_are_supertypes(self):
        generic_class = types.generic_class("iterator", [types.contravariant("T")])
        
        assert not types.is_sub_type(generic_class(types.object_type), generic_class(types.int_type))
        assert types.is_sub_type(generic_class(types.int_type), generic_class(types.object_type))
    
    @istest
    def scalar_type_is_not_sub_type_of_formal_type_parameter(self):
        assert not types.is_sub_type(_formal_param, _scalar_type)
    
    @istest
    def scalar_type_is_not_super_type_of_formal_type_parameter(self):
        assert not types.is_sub_type(_scalar_type, _formal_param)
    
    @istest
    def formal_type_can_be_super_type_of_formal_param_if_formal_param_can_be_unified(self):
        assert types.is_sub_type(_formal_param, _scalar_type, unify=[_formal_param])
    
    @istest
    def formal_type_can_be_sub_type_of_formal_param_if_formal_param_can_be_unified(self):
        assert types.is_sub_type(_scalar_type, _formal_param, unify=[_formal_param])
    
    @istest
    def type_map_is_returned_by_sub_type_unification(self):
        type_map = types.is_sub_type(_formal_param, _scalar_type, unify=[_formal_param])
        assert_equal(_scalar_type, type_map[_formal_param])
    
    @istest
    def type_map_is_returned_by_super_type_unification(self):
        type_map = types.is_sub_type(_scalar_type, _formal_param, unify=[_formal_param])
        assert_equal(_scalar_type, type_map[_formal_param])
    
    @istest
    def unification_occurs_before_reification(self):
        instantiated_type = types.generic_class("blah", ["T"])(int_type)
        type_map = types.is_sub_type(_formal_param, instantiated_type, unify=[_formal_param])
        assert_equal(instantiated_type, type_map[_formal_param])
    
    @istest
    def invariant_type_parameter_cannot_have_different_values_in_same_is_sub_type_relation(self):
        invariant_type_param = types.invariant("T")
        first_scalar_type = types.scalar_type("User")
        second_scalar_type = types.scalar_type("Role")
        generic_class = types.generic_class("Pair", [invariant_type_param, invariant_type_param])
        assert not types.is_sub_type(
            # TODO: need a reliable way of getting the underlying type (but as an instantiated type)
            generic_class(invariant_type_param, invariant_type_param),
            generic_class(first_scalar_type, second_scalar_type),
            unify=[invariant_type_param]
        )
    
    @istest
    def covariant_type_parameter_is_substituted_with_common_super_type_of_actual_type_params(self):
        covariant_type_param = types.covariant("T")
        first_scalar_type = types.scalar_type("User")
        second_scalar_type = types.scalar_type("Role")
        generic_class = types.generic_class("Pair", [covariant_type_param, covariant_type_param])
        
        type_map = types.is_sub_type(
            # TODO: need a reliable way of getting the underlying type (but as an instantiated type)
            generic_class(covariant_type_param, covariant_type_param),
            generic_class(first_scalar_type, second_scalar_type),
            unify=[covariant_type_param]
        )
        assert_equal(types.union(first_scalar_type, second_scalar_type), type_map[covariant_type_param])
    
    @istest
    def contravariant_type_parameter_is_substituted_with_common_sub_type_of_actual_type_params(self):
        contravariant_type_param = types.contravariant("T")
        first_scalar_type = types.scalar_type("User")
        second_scalar_type = types.scalar_type("Role")
        generic_class = types.generic_class("Pair", [contravariant_type_param, contravariant_type_param])
        
        type_map = types.is_sub_type(
            # TODO: need a reliable way of getting the underlying type (but as an instantiated type)
            generic_class(contravariant_type_param, contravariant_type_param),
            generic_class(first_scalar_type, second_scalar_type),
            unify=[contravariant_type_param]
        )
        assert_equal(types.bottom_type, type_map[contravariant_type_param])
        
    @istest
    def invariant_type_parameter_can_be_unified_when_part_of_recursive_structural_type(self):
        invariant_type_param = types.invariant("T")
        recursive = types.generic_structural_type("recursive", [types.covariant("T")], lambda T: [
            types.attr("__iter__", types.func([], recursive(T))),
        ])
        
        assert types.is_sub_type(
            recursive(invariant_type_param),
            recursive(types.int_type),
            unify=[invariant_type_param]
        )
        
    @istest
    def func_type_is_sub_type_of_itself(self):
        func_type = lambda: types.func([int_type], str_type)
        
        assert types.is_sub_type(func_type(), func_type())
        
    @istest
    def func_type_is_not_sub_type_if_it_has_different_number_of_arguments(self):
        short_func_type = types.func([], str_type)
        long_func_type = types.func([int_type], str_type)
        
        assert not types.is_sub_type(short_func_type, long_func_type)
        assert not types.is_sub_type(long_func_type, short_func_type)
        
    @istest
    def func_type_is_not_sub_type_if_argument_has_different_name(self):
        first_func_type = types.func([types.func_arg("x", int_type)], str_type)
        second_func_type = types.func([types.func_arg("y", int_type)], str_type)
        
        assert not types.is_sub_type(first_func_type, second_func_type)
        assert not types.is_sub_type(second_func_type, first_func_type)
        
    @istest
    def func_type_is_sub_type_if_argument_of_super_type_has_no_name_and_sub_type_has_name(self):
        first_func_type = types.func([types.func_arg(None, int_type)], str_type)
        second_func_type = types.func([types.func_arg("y", int_type)], str_type)
        
        assert types.is_sub_type(first_func_type, second_func_type)
        assert not types.is_sub_type(second_func_type, first_func_type)
        
    @istest
    def functions_are_contravariant_in_their_arguments(self):
        super_type = types.func([int_type], str_type)
        sub_type = types.func([types.object_type], str_type)
        
        assert types.is_sub_type(super_type, sub_type)
        assert not types.is_sub_type(sub_type, super_type)
        
    @istest
    def functions_are_covariant_in_return_type(self):
        super_type = types.func([int_type], types.object_type)
        sub_type = types.func([int_type], str_type)
        
        assert types.is_sub_type(super_type, sub_type)
        assert not types.is_sub_type(sub_type, super_type)
        
    @istest
    def any_meta_type_is_super_type_of_meta_types(self):
        assert types.is_sub_type(types.any_meta_type, types.meta_type(types.int_type))
        assert not types.is_sub_type(types.meta_type(types.int_type), types.any_meta_type)
        
    @istest
    def any_meta_type_is_not_super_type_of_non_meta_types(self):
        assert not types.is_sub_type(types.any_meta_type, types.int_type)


@istest
class CommonSuperTypeTests(object):
    @istest
    def common_super_type_of_one_type_is_same_type(self):
        assert_equal(types.none_type, types.common_super_type([types.none_type]))
        
    @istest
    def common_super_type_of_zero_types_is_bottom_type(self):
        assert_equal(types.bottom_type, types.common_super_type([]))
        
    @istest
    def common_super_type_of_types_is_object_if_any_type_is_object(self):
        assert_equal(types.object_type, types.common_super_type([types.int_type, types.object_type]))
        
    @istest
    def common_super_type_of_types_is_passed_type_that_is_super_type_of_all_other_types(self):
        first_type = types.structural_type("first", [
            types.attr("a", types.int_type),
            types.attr("b", types.str_type),
        ])
        second_type = types.structural_type("second", [
            types.attr("a", types.int_type),
        ])
        assert_equal(second_type, types.common_super_type([first_type, second_type]))
        
    @istest
    def common_super_type_of_unrelated_types_is_union_of_those_types(self):
        assert_equal(
            types.union(types.int_type, types.str_type),
            types.common_super_type([types.int_type, types.str_type]),
        )
        

@istest
class IsFuncTypeTests(object):
    @istest
    def func_type_is_func_type(self):
        func_type = types.func([], types.none_type)
        assert types.is_func_type(func_type)

    @istest
    def scalar_type_is_not_func_type(self):
        scalar_type = types.scalar_type("A")
        assert not types.is_func_type(scalar_type)

    @istest
    def scalar_type_with_call_magic_method_is_not_func_type(self):
        scalar_type = types.scalar_type("A", [
            types.attr("__call__", types.func([], types.none_type)),
        ])
        assert not types.is_func_type(scalar_type)
        
@istest
class GenericTypeTests(object):
    @istest
    def instantiated_type_includes_names_of_actual_type_parameters(self):
        assert_equal("Option[int]", str(types.generic_class("Option", ["T"])(int_type)))
            
    @istest
    def cannot_instantiate_generic_type_with_wrong_number_of_type_parameters(self):
        generic_type = types.generic_class("Option", ["T"])
        try:
            generic_type(types.int_type, types.int_type)
            assert False, "Expected error"
        except Exception as error:
            assert_equal("generic type requires exactly 1 type parameter(s)", str(error))
    
    @istest
    def type_is_instance_of_generic_type_when_type_is_direct_instantiation(self):
        generic_type = types.generic_structural_type("box", ["T"], lambda T: [
            types.attr("value", T)
        ])
        scalar_type = types.scalar_type("boxed_int", [types.attr("value", "int")])
        
        assert generic_type.is_instantiated_type(generic_type(types.int_type))
        assert not generic_type.is_instantiated_type(scalar_type)
    
    @istest
    def type_is_subtype_instance_of_generic_type_when_type_is_not_direct_instantiation(self):
        generic_type = types.generic_structural_type("box", ["T"], lambda T: [
            types.attr("value", T)
        ])
        scalar_type = types.scalar_type("boxed_int", [types.attr("value", "int")])
        
        assert generic_type.is_instantiated_sub_type(scalar_type)
        assert generic_type.is_instantiated_sub_type(generic_type(types.int_type))
        assert not generic_type.is_instantiated_sub_type(types.scalar_type("empty"))
    
    @istest
    def instantiating_type_replaces_type_in_attributes(self):
        generic_type = types.generic_structural_type("box", ["T"], lambda T: [
            types.attr("value", T)
        ])
        assert_equal(int_type, generic_type(int_type).attrs.type_of("value"))
    
    @istest
    def instantiating_type_replaces_type_in_attributes_of_instantiated_attributes(self):
        one = types.generic_class("one", ["A"])
        two = types.generic_class("two", ["B"])
        three = types.generic_class("three", ["C"], lambda C: [
            types.attr("value", one(two(C))),
        ])
        assert_equal(
            one(two(types.int_type)),
            three(types.int_type).attrs.type_of("value"),
        )


@istest
class UnionTypeTests(object):
    @istest
    def duplicate_types_are_collapsed_in_type_union(self):
        assert_equal(types.int_type, types.union(types.int_type, types.int_type))
