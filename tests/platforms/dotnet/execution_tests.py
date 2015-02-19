import os

import tempman
from nose.tools import istest

from nope.platforms.dotnet import DotNet
from .. import execution
#from ...testing import wip
def wip(*args):
    return None

@istest
class DotNetExecutionTests(execution.ExecutionTests):
    platform = DotNet
    
    can_import_local_module = wip(execution.ExecutionTests.can_import_local_module)
    can_import_local_package = wip(execution.ExecutionTests.can_import_local_package)
    can_import_module_in_package = wip(execution.ExecutionTests.can_import_module_in_package)
    can_import_module_in_package_using_import_from = wip(execution.ExecutionTests.can_import_module_in_package_using_import_from)
    can_import_value_from_local_package = wip(execution.ExecutionTests.can_import_value_from_local_package)
    can_read_attributes_of_builtins = wip(execution.ExecutionTests.can_read_attributes_of_builtins)
    fib_program_prints_result_to_stdout = wip(execution.ExecutionTests.fib_program_prints_result_to_stdout)
    functions_can_be_defined_out_of_order = wip(execution.ExecutionTests.functions_can_be_defined_out_of_order)
    test_assert_false_with_message = wip(execution.ExecutionTests.test_assert_false_with_message)
    test_assert_false_without_message = wip(execution.ExecutionTests.test_assert_false_without_message)
    test_assert_true_shows_no_output = wip(wip(execution.ExecutionTests.test_assert_true_shows_no_output))
    test_bool_and = wip(execution.ExecutionTests.test_bool_and)
    test_bool_or = wip(execution.ExecutionTests.test_bool_or)
    test_call_method_of_class_with_default_constructor = wip(execution.ExecutionTests.test_call_method_of_class_with_default_constructor)
    test_first_matching_exception_handler_runs_first = wip(execution.ExecutionTests.test_first_matching_exception_handler_runs_first)
    test_for_unpacking = wip(execution.ExecutionTests.test_for_unpacking)
    test_generic_class_type_parameters_are_inferred_from_init_method = wip(execution.ExecutionTests.test_generic_class_type_parameters_are_inferred_from_init_method)
    test_getitem_dict = wip(execution.ExecutionTests.test_getitem_dict)
    test_getitem_list = wip(execution.ExecutionTests.test_getitem_list)
    test_getitem_list_with_negative_integer = wip(execution.ExecutionTests.test_getitem_list_with_negative_integer)
    test_import_of_module_in_standard_library = wip(execution.ExecutionTests.test_import_of_module_in_standard_library)
    test_in_operator_list = wip(execution.ExecutionTests.test_in_operator_list)
    test_init_method_is_used_to_construct_instance = wip(execution.ExecutionTests.test_init_method_is_used_to_construct_instance)
    test_method_can_call_function_defined_later = wip(execution.ExecutionTests.test_method_can_call_function_defined_later)
    test_output_of_bool = wip(execution.ExecutionTests.test_output_of_bool)
    test_settitem_list = wip(execution.ExecutionTests.test_settitem_list)
    test_slice_list = wip(execution.ExecutionTests.test_slice_list)
    test_slice_list_swaps_default_start_and_stop_when_step_is_negative = wip(execution.ExecutionTests.test_slice_list_swaps_default_start_and_stop_when_step_is_negative)
    test_slice_list_with_negative_step_reverses_direction_of_list = wip(execution.ExecutionTests.test_slice_list_with_negative_step_reverses_direction_of_list)
    test_slice_list_with_slice_start = wip(execution.ExecutionTests.test_slice_list_with_slice_start)
    test_slice_list_with_slice_step = wip(execution.ExecutionTests.test_slice_list_with_slice_step)
    test_slice_list_with_slice_stop = wip(execution.ExecutionTests.test_slice_list_with_slice_stop)
    test_transformer_for_collections_namedtuple = wip(execution.ExecutionTests.test_transformer_for_collections_namedtuple)
    test_try_except_finally_with_exception = wip(execution.ExecutionTests.test_try_except_finally_with_exception)
    test_try_except_finally_with_no_exception = wip(execution.ExecutionTests.test_try_except_finally_with_no_exception)
    test_try_except_with_exception_handles_subexception = wip(execution.ExecutionTests.test_try_except_with_exception_handles_subexception)
    test_try_except_with_exception_ignores_superexception = wip(execution.ExecutionTests.test_try_except_with_exception_ignores_superexception)
    test_try_named_except_finally_with_exception = wip(execution.ExecutionTests.test_try_named_except_finally_with_exception)
    test_unhandled_exception = wip(execution.ExecutionTests.test_unhandled_exception)
    test_unnested_generator_expression = wip(execution.ExecutionTests.test_unnested_generator_expression)
    test_unnested_list_comprehension = wip(execution.ExecutionTests.test_unnested_list_comprehension)
    test_with_statement_calls_enter_and_exit_methods_when_body_exits_normally = wip(execution.ExecutionTests.test_with_statement_calls_enter_and_exit_methods_when_body_exits_normally)
    test_with_statement_does_not_suppress_exception_when_exit_returns_false = wip(execution.ExecutionTests.test_with_statement_does_not_suppress_exception_when_exit_returns_false)
    test_with_statement_passes_exception_info_to_exit_method_if_body_raises_exception = wip(execution.ExecutionTests.test_with_statement_passes_exception_info_to_exit_method_if_body_raises_exception)
    test_with_statement_suppresses_exception_when_exit_returns_true = wip(execution.ExecutionTests.test_with_statement_suppresses_exception_when_exit_returns_true)
