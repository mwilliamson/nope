from nose.tools import istest, assert_equal

from nope import parser, nodes


@istest
def can_parse_function_definition():
    source = """
def f():
    pass
"""
    
    module_node = parser.parse(source)
    assert_equal(nodes.func("f", nodes.args([]), None, []), module_node.body[0])


@istest
def can_parse_argument_and_return_annotations():
    source = """
def f(x: int) -> str:
    pass
"""
    
    module_node = parser.parse(source)
    arg = nodes.arg("x", nodes.ref("int"))
    expected = nodes.func("f", nodes.args([arg]), nodes.ref("str"), [])
    assert_equal(expected, module_node.body[0])


@istest
def can_parse_signature_comment_with_no_args():
    source = """
#:: -> str
def f():
    pass
"""
    
    module_node = parser.parse(source)
    expected = nodes.func("f", nodes.args([]), nodes.ref("str"), [])
    assert_equal(expected, module_node.body[0])


@istest
def can_parse_signature_comment_with_no_args_for_function_after_indent():
    source = """
#:: -> str
def f():
    #:: -> int
    def g():
        pass
"""
    
    module_node = parser.parse(source)
    expected = nodes.func("g", nodes.args([]), nodes.ref("int"), [])
    assert_equal(expected, module_node.body[0].body[0])


@istest
def can_parse_signature_comment_with_no_args_for_function_after_dedent():
    source = """
#:: -> str
def f():
    pass
    
#:: -> int
def g():
    pass
"""
    
    module_node = parser.parse(source)
    expected = nodes.func("g", nodes.args([]), nodes.ref("int"), [])
    assert_equal(expected, module_node.body[1])


@istest
def can_parse_signature_comment_with_one_arg():
    source = """
#:: int -> str
def f(x):
    pass
"""
    
    module_node = parser.parse(source)
    arg = nodes.arg("x", nodes.ref("int"))
    expected = nodes.func("f", nodes.args([arg]), nodes.ref("str"), [])
    assert_equal(expected, module_node.body[0])



@istest
def can_parse_signature_comment_with_multiple_args():
    source = """
#:: int, str -> str
def f(x, y):
    pass
"""
    
    module_node = parser.parse(source)
    args = nodes.args([
        nodes.arg("x", nodes.ref("int")),
        nodes.arg("y", nodes.ref("str")),
    ])
    expected = nodes.func("f", args, nodes.ref("str"), [])
    assert_equal(expected, module_node.body[0])


@istest
def can_parse_signature_comment_with_type_application_with_one_generic_parameter():
    source = """
#:: -> list[str]
def f():
    pass
"""
    
    module_node = parser.parse(source)
    return_node = nodes.type_apply(nodes.ref("list"), [nodes.ref("str")])
    expected = nodes.func("f", nodes.args([]), return_node, [])
    assert_equal(expected, module_node.body[0])



@istest
def can_parse_signature_comment_with_type_application_with_many_generic_parameters():
    source = """
#:: -> dict[str, int]
def f():
    pass
"""
    
    module_node = parser.parse(source)
    return_node = nodes.type_apply(nodes.ref("dict"), [nodes.ref("str"), nodes.ref("int")])
    expected = nodes.func("f", nodes.args([]), return_node, [])
    assert_equal(expected, module_node.body[0])


@istest
def can_parse_signature_comment_with_one_formal_type_parameter():
    source = """
#:: T => T -> T
def f(x):
    return x
"""
    
    module_node = parser.parse(source)
    expected = nodes.func(
        "f",
        nodes.args([nodes.arg("x", nodes.ref("T"))]),
        nodes.ref("T"),
        [nodes.ret(nodes.ref("x"))],
        ["T"],
    )
    assert_equal(expected, module_node.body[0])
