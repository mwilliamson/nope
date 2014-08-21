from nose.tools import istest, assert_equal

from nope import util, nodes, errors


@istest
def declared_locals_removes_duplicate_names():
    statements = [
        nodes.assign("x", nodes.int(1)),
        nodes.assign("x", nodes.int(2)),
    ]
    assert_equal(["x"], list(util.declared_locals(statements)))


@istest
def declared_names_includes_names_from_both_branches_of_if_else_statement():
    if_else = nodes.if_else(
        nodes.int(1),
        [nodes.assign("x", nodes.int(2)), nodes.assign("y", nodes.int(4))],
        [nodes.assign("z", nodes.ref("a"))],
    )
    assert_equal(["x", "y", "z"], list(util.declared_names(if_else)))


@istest
def declared_names_removes_duplicates():
    if_else = nodes.if_else(
        nodes.int(1),
        [nodes.assign("x", nodes.int(2))],
        [nodes.assign("x", nodes.ref("a"))],
    )
    assert_equal(["x"], list(util.declared_names(if_else)))


@istest
def declared_names_includes_target_of_for_loop():
    for_loop = nodes.for_loop(
        nodes.ref("x"),
        nodes.ref("xs"),
        [],
    )
    assert_equal(["x"], list(util.declared_names(for_loop)))


@istest
def declared_names_includes_names_in_for_loop_body():
    for_loop = nodes.for_loop(
        nodes.ref("x"),
        nodes.ref("xs"),
        [nodes.assign("y", nodes.none())],
    )
    assert_equal(["x", "y"], list(util.declared_names(for_loop)))


@istest
def declared_names_includes_names_in_while_loop_bodies():
    while_loop = nodes.while_loop(
        nodes.ref("x"),
        [nodes.assign("x", nodes.none())],
        [nodes.assign("y", nodes.none())],
    )
    assert_equal(["x", "y"], list(util.declared_names(while_loop)))


@istest
def declared_names_includes_names_in_try_bodies():
    statement = nodes.try_statement(
        [nodes.assign("x", nodes.none())],
        handlers=[
            nodes.except_handler(nodes.ref("Exception"), "error", [nodes.assign("y", nodes.none())]),
        ],
        finally_body=[nodes.assign("z", nodes.none())],
    )
    assert_equal(["x", "error", "y", "z"], list(util.declared_names(statement)))


@istest
def except_handler_can_have_no_name():
    statement = nodes.try_statement(
        [nodes.assign("x", nodes.none())],
        handlers=[
            nodes.except_handler(None, None, [nodes.assign("y", nodes.none())]),
        ],
        finally_body=[nodes.assign("z", nodes.none())],
    )
    assert_equal(["x", "y", "z"], list(util.declared_names(statement)))


@istest
def declared_names_includes_names_in_with_bodies():
    statement = nodes.with_statement(
        nodes.ref("manager"),
        None,
        [nodes.assign("x", nodes.none())],
    )
    assert_equal(["x"], list(util.declared_names(statement)))


@istest
def declared_names_includes_target_of_with_statement():
    statement = nodes.with_statement(
        nodes.ref("manager"),
        nodes.ref("value"),
        [],
    )
    assert_equal(["value"], list(util.declared_names(statement)))


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
        all_node = nodes.assign(["__all__"], nodes.list([nodes.none()]))
        util.exported_names(nodes.module([all_node]))
        assert False, "Expected error"
    except errors.AllAssignmentError as error:
        assert_equal(all_node, error.node)
        assert_equal("__all__ must be a list of string literals", str(error))



@istest
def error_is_raised_if_all_is_redeclared():
    try:
        all_node = nodes.assign(["__all__"], nodes.list([]))
        second_all_node = nodes.assign(["__all__"], nodes.list([]))
        util.exported_names(nodes.module([all_node, second_all_node]))
        assert False, "Expected error"
    except errors.AllAssignmentError as error:
        assert_equal(second_all_node, error.node)
        assert_equal("__all__ cannot be redeclared", str(error))
