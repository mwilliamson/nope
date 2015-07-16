from nose.tools import istest

from nope import nodes
from nope.inference.literals import is_literal


@istest
class IsLiteralTests(object):
    @istest
    def reference_is_not_literal(self):
        assert not is_literal(nodes.ref("x"))
        
    @istest
    def none_is_literal(self):
        assert is_literal(nodes.none())
        
    @istest
    def boolean_is_literal(self):
        assert is_literal(nodes.bool_literal(True))
        
    @istest
    def str_is_literal(self):
        assert is_literal(nodes.str_literal(""))
        
    @istest
    def int_is_literal(self):
        assert is_literal(nodes.int_literal(42))
        
    @istest
    def empty_list_is_literal(self):
        assert is_literal(nodes.list_literal([]))
        
    @istest
    def list_containing_reference_is_not_literal(self):
        assert not is_literal(nodes.list_literal([nodes.ref("x")]))
        
    @istest
    def list_containing_literal_is_literal(self):
        assert is_literal(nodes.list_literal([nodes.none()]))
        
    @istest
    def empty_tuple_is_literal(self):
        assert is_literal(nodes.tuple_literal([]))
        
    @istest
    def tuple_containing_reference_is_not_literal(self):
        assert not is_literal(nodes.tuple_literal([nodes.ref("x")]))
        
    @istest
    def tuple_containing_literal_is_literal(self):
        assert is_literal(nodes.tuple_literal([nodes.none()]))
