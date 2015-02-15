import os

import tempman
from nose.tools import istest

from nope.platforms.dotnet import DotNet
from .. import execution
from ...testing import wip


@istest
class DotNetExecutionTests(execution.ExecutionTests):
    platform = DotNet
    
    can_call_generic_identity_function = wip(execution.ExecutionTests.can_call_generic_identity_function)
    can_import_local_module = wip(execution.ExecutionTests.can_import_local_module)
    can_import_local_package = wip(execution.ExecutionTests.can_import_local_package)
    can_import_module_in_package = wip(execution.ExecutionTests.can_import_module_in_package)
    can_import_module_in_package_using_import_from = wip(execution.ExecutionTests.can_import_module_in_package_using_import_from)
    can_import_value_from_local_package = wip(execution.ExecutionTests.can_import_value_from_local_package)
    can_read_attributes_of_builtins = wip(execution.ExecutionTests.can_read_attributes_of_builtins)
    fib_program_prints_result_to_stdout = wip(execution.ExecutionTests.fib_program_prints_result_to_stdout)
    function_call_with_default_value = wip(execution.ExecutionTests.function_call_with_default_value)
    function_calls = wip(execution.ExecutionTests.function_calls)
    function_calls_with_generics = wip(execution.ExecutionTests.function_calls_with_generics)
    function_definition_with_if_none_assignment = wip(execution.ExecutionTests.function_definition_with_if_none_assignment)
    function_definition_with_if_not_none_branch = wip(execution.ExecutionTests.function_definition_with_if_not_none_branch)
    functions_can_be_defined_out_of_order = wip(execution.ExecutionTests.functions_can_be_defined_out_of_order)
    print_def_program_prints_to_stdout = wip(execution.ExecutionTests.print_def_program_prints_to_stdout)
    print_program_prints_to_stdout = wip(execution.ExecutionTests.print_program_prints_to_stdout)
    test_abs_int = wip(execution.ExecutionTests.test_abs_int)
    test_add_int = wip(execution.ExecutionTests.test_add_int)
    test_arithmetic = wip(execution.ExecutionTests.test_arithmetic)
    test_assert_false_with_message = wip(execution.ExecutionTests.test_assert_false_with_message)
    test_assert_false_without_message = wip(execution.ExecutionTests.test_assert_false_without_message)
    test_assert_true_shows_no_output = wip(wip(execution.ExecutionTests.test_assert_true_shows_no_output))
    test_bitwise_and_int = wip(execution.ExecutionTests.test_bitwise_and_int)
    test_bitwise_or_int = wip(execution.ExecutionTests.test_bitwise_or_int)
    test_bitwise_xor_int = wip(execution.ExecutionTests.test_bitwise_xor_int)
    test_bool_and = wip(execution.ExecutionTests.test_bool_and)
    test_bool_not = wip(execution.ExecutionTests.test_bool_not)
    test_bool_or = wip(execution.ExecutionTests.test_bool_or)
    test_break_for = wip(execution.ExecutionTests.test_break_for)
    test_call_int_magic_method_directly = wip(execution.ExecutionTests.test_call_int_magic_method_directly)
    test_call_method_of_class_with_default_constructor = wip(execution.ExecutionTests.test_call_method_of_class_with_default_constructor)
    test_continue_for = wip(execution.ExecutionTests.test_continue_for)
    test_divmod_int = wip(execution.ExecutionTests.test_divmod_int)
    test_eq_int = wip(execution.ExecutionTests.test_eq_int)
    test_first_matching_exception_handler_runs_first = wip(execution.ExecutionTests.test_first_matching_exception_handler_runs_first)
    test_floordiv_int = wip(execution.ExecutionTests.test_floordiv_int)
    test_for = wip(execution.ExecutionTests.test_for)
    test_for_else = wip(execution.ExecutionTests.test_for_else)
    test_for_else_break = wip(execution.ExecutionTests.test_for_else_break)
    test_for_else_continue = wip(execution.ExecutionTests.test_for_else_continue)
    test_for_unpacking = wip(execution.ExecutionTests.test_for_unpacking)
    test_ge_int = wip(execution.ExecutionTests.test_ge_int)
    test_generic_class_type_parameters_are_inferred_from_init_method = wip(execution.ExecutionTests.test_generic_class_type_parameters_are_inferred_from_init_method)
    test_getitem_dict = wip(execution.ExecutionTests.test_getitem_dict)
    test_getitem_list = wip(execution.ExecutionTests.test_getitem_list)
    test_getitem_list_with_negative_integer = wip(execution.ExecutionTests.test_getitem_list_with_negative_integer)
    test_gt_int = wip(execution.ExecutionTests.test_gt_int)
    test_import_of_module_in_standard_library = wip(execution.ExecutionTests.test_import_of_module_in_standard_library)
    test_in_operator_list = wip(execution.ExecutionTests.test_in_operator_list)
    test_init_method_is_used_to_construct_instance = wip(execution.ExecutionTests.test_init_method_is_used_to_construct_instance)
    test_invert_int = wip(execution.ExecutionTests.test_invert_int)
    test_is = wip(execution.ExecutionTests.test_is)
    test_is_not = wip(execution.ExecutionTests.test_is_not)
    test_le_int = wip(execution.ExecutionTests.test_le_int)
    test_lshift_int = wip(execution.ExecutionTests.test_lshift_int)
    test_lt_int = wip(execution.ExecutionTests.test_lt_int)
    test_method_can_call_function_defined_later = wip(execution.ExecutionTests.test_method_can_call_function_defined_later)
    test_mod_int = wip(execution.ExecutionTests.test_mod_int)
    test_mul_int = wip(execution.ExecutionTests.test_mul_int)
    test_ne_int = wip(execution.ExecutionTests.test_ne_int)
    test_neg_int = wip(execution.ExecutionTests.test_neg_int)
    test_output_of_bool = wip(execution.ExecutionTests.test_output_of_bool)
    test_pos_int = wip(execution.ExecutionTests.test_pos_int)
    test_pow_int = wip(execution.ExecutionTests.test_pow_int)
    test_rshift_int = wip(execution.ExecutionTests.test_rshift_int)
    test_settitem_list = wip(execution.ExecutionTests.test_settitem_list)
    test_slice_list = wip(execution.ExecutionTests.test_slice_list)
    test_slice_list_swaps_default_start_and_stop_when_step_is_negative = wip(execution.ExecutionTests.test_slice_list_swaps_default_start_and_stop_when_step_is_negative)
    test_slice_list_with_negative_step_reverses_direction_of_list = wip(execution.ExecutionTests.test_slice_list_with_negative_step_reverses_direction_of_list)
    test_slice_list_with_slice_start = wip(execution.ExecutionTests.test_slice_list_with_slice_start)
    test_slice_list_with_slice_step = wip(execution.ExecutionTests.test_slice_list_with_slice_step)
    test_slice_list_with_slice_stop = wip(execution.ExecutionTests.test_slice_list_with_slice_stop)
    test_sub_int = wip(execution.ExecutionTests.test_sub_int)
    test_transformer_for_collections_namedtuple = wip(execution.ExecutionTests.test_transformer_for_collections_namedtuple)
    test_truediv_int = wip(execution.ExecutionTests.test_truediv_int)
    test_try_except_finally_with_exception = wip(execution.ExecutionTests.test_try_except_finally_with_exception)
    test_try_except_finally_with_no_exception = wip(execution.ExecutionTests.test_try_except_finally_with_no_exception)
    test_try_except_with_exception_handles_subexception = wip(execution.ExecutionTests.test_try_except_with_exception_handles_subexception)
    test_try_except_with_exception_ignores_superexception = wip(execution.ExecutionTests.test_try_except_with_exception_ignores_superexception)
    test_try_named_except_finally_with_exception = wip(execution.ExecutionTests.test_try_named_except_finally_with_exception)
    test_unhandled_exception = wip(execution.ExecutionTests.test_unhandled_exception)
    test_unnested_generator_expression = wip(execution.ExecutionTests.test_unnested_generator_expression)
    test_unnested_list_comprehension = wip(execution.ExecutionTests.test_unnested_list_comprehension)
    test_while = wip(execution.ExecutionTests.test_while)
    test_while_else = wip(execution.ExecutionTests.test_while_else)
    test_while_else_break = wip(execution.ExecutionTests.test_while_else_break)
    test_while_else_continue = wip(execution.ExecutionTests.test_while_else_continue)
    test_with_statement_calls_enter_and_exit_methods_when_body_exits_normally = wip(execution.ExecutionTests.test_with_statement_calls_enter_and_exit_methods_when_body_exits_normally)
    test_with_statement_does_not_suppress_exception_when_exit_returns_false = wip(execution.ExecutionTests.test_with_statement_does_not_suppress_exception_when_exit_returns_false)
    test_with_statement_passes_exception_info_to_exit_method_if_body_raises_exception = wip(execution.ExecutionTests.test_with_statement_passes_exception_info_to_exit_method_if_body_raises_exception)
    test_with_statement_suppresses_exception_when_exit_returns_true = wip(execution.ExecutionTests.test_with_statement_suppresses_exception_when_exit_returns_true)
    type_definition_using_type_union = wip(execution.ExecutionTests.type_definition_using_type_union)
