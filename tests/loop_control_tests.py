from nose.tools import istest


from nose.tools import istest, assert_equal

from nope import types, nodes, errors
from nope.loop_control import check_loop_control


@istest
def break_is_not_valid_in_module():
    node = nodes.break_statement()
    try:
        check_loop_control(node, False)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(node, error.node)
        assert_equal("'break' outside loop", str(error))


@istest
def break_is_valid_in_for_loop_body():
    node = nodes.for_loop(nodes.ref("x"), nodes.ref("xs"), [nodes.break_statement()])
    check_loop_control(node, False)


@istest
def break_is_valid_in_while_loop_body():
    node = nodes.while_loop(nodes.boolean(True), [nodes.break_statement()])
    check_loop_control(node, False)


@istest
def break_is_not_valid_in_while_loop_else_body():
    break_node = nodes.break_statement()
    node = nodes.while_loop(nodes.boolean(True), [], [break_node])
    try:
        check_loop_control(node, False)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(break_node, error.node)
        assert_equal("'break' outside loop", str(error))


@istest
def break_is_not_valid_in_function_in_while_loop_body():
    break_node = nodes.break_statement()
    func_node = nodes.func("f", None, nodes.args([]), [break_node])
    node = nodes.while_loop(nodes.boolean(True), [func_node], [])
    try:
        check_loop_control(node, False)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(break_node, error.node)
        assert_equal("'break' outside loop", str(error))


@istest
def continue_is_not_valid_in_module():
    node = nodes.continue_statement()
    try:
        check_loop_control(node, False)
        assert False, "Expected error"
    except errors.TypeCheckError as error:
        assert_equal(node, error.node)
        assert_equal("'continue' outside loop", str(error))

