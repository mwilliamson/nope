from nose.tools import istest, assert_equal

from nope import util, nodes, errors


@istest
def error_is_raised_if_all_is_not_a_list():
    try:
        all_node = nodes.assign(["__all__"], nodes.none())
        util.exported_names(nodes.module([all_node]))
        assert False, "Expected error"
    except errors.AllAssignmentError as error:
        assert_equal(all_node, error.node)
        assert_equal("__all__ must be a list of string literals", str(error))


@istest
def error_is_raised_if_all_does_not_contain_only_string_literals():
    try:
        all_node = nodes.assign(["__all__"], nodes.list_literal([nodes.none()]))
        util.exported_names(nodes.module([all_node]))
        assert False, "Expected error"
    except errors.AllAssignmentError as error:
        assert_equal(all_node, error.node)
        assert_equal("__all__ must be a list of string literals", str(error))



@istest
def error_is_raised_if_all_is_redeclared():
    try:
        all_node = nodes.assign(["__all__"], nodes.list_literal([]))
        second_all_node = nodes.assign(["__all__"], nodes.list_literal([]))
        util.exported_names(nodes.module([all_node, second_all_node]))
        assert False, "Expected error"
    except errors.AllAssignmentError as error:
        assert_equal(second_all_node, error.node)
        assert_equal("__all__ cannot be redeclared", str(error))
