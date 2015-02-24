from nose.tools import istest, assert_equal

from nope import nodes, errors
from nope.loop_control import check_loop_control


@istest
def break_is_not_valid_in_module():
    node = nodes.break_()
    try:
        check_loop_control(node, False)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(node, error.node)
        assert_equal("'break' outside loop", str(error))


@istest
def break_is_valid_in_for_loop_body():
    node = nodes.for_(nodes.ref("x"), nodes.ref("xs"), [nodes.break_()])
    check_loop_control(node, False)


@istest
def break_is_valid_in_while_loop_body():
    node = nodes.while_(nodes.bool_literal(True), [nodes.break_()])
    check_loop_control(node, False)


@istest
def break_is_not_valid_in_while_loop_else_body():
    break_node = nodes.break_()
    node = nodes.while_(nodes.bool_literal(True), [], [break_node])
    try:
        check_loop_control(node, False)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(break_node, error.node)
        assert_equal("'break' outside loop", str(error))


@istest
def break_is_not_valid_in_function_in_while_loop_body():
    break_node = nodes.break_()
    func_node = nodes.func("f", nodes.args([]), [break_node])
    node = nodes.while_(nodes.bool_literal(True), [func_node], [])
    try:
        check_loop_control(node, False)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(break_node, error.node)
        assert_equal("'break' outside loop", str(error))


@istest
def break_is_not_valid_in_class_in_while_loop_body():
    break_node = nodes.break_()
    func_node = nodes.class_("User", [break_node])
    node = nodes.while_(nodes.bool_literal(True), [func_node], [])
    try:
        check_loop_control(node, False)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(break_node, error.node)
        assert_equal("'break' outside loop", str(error))


@istest
def break_is_valid_in_try_finally_body():
    node = nodes.try_([], finally_body=[nodes.break_()])
    check_loop_control(node, True)


@istest
def continue_is_not_valid_in_module():
    node = nodes.continue_()
    try:
        check_loop_control(node, False)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(node, error.node)
        assert_equal("'continue' outside loop", str(error))


@istest
def continue_is_valid_in_try_body():
    node = nodes.try_([nodes.continue_()])
    check_loop_control(node, True)


@istest
def continue_is_not_valid_in_try_finally_body():
    continue_statement = nodes.continue_()
    node = nodes.try_([], finally_body=[continue_statement])
    try:
        check_loop_control(node, True)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(continue_statement, error.node)
        assert_equal("'continue' not supported inside 'finally' clause", str(error))
