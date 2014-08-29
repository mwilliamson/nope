import io

from nose.tools import istest, assert_equal

from nope import textseek


@istest
def test_seek_first_line_of_text():
    text = io.StringIO("one\ntwo\nthree")
    assert_equal("one", textseek.seek_line(text, 1))


@istest
def test_seek_line_of_text_in_middle():
    text = io.StringIO("one\ntwo\nthree")
    assert_equal("two", textseek.seek_line(text, 2))



@istest
def test_seek_last_line_of_text():
    text = io.StringIO("one\ntwo\nthree")
    assert_equal("three", textseek.seek_line(text, 3))
