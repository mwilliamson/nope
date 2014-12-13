import os

from nose.tools import istest, assert_equal, assert_raises_regexp
import tempman

from nope import paths


@istest
class FindFilesTests(object):
    def setup(self):
        self._temp_dir = tempman.create_temp_dir()
    
    def teardown(self):
        self._temp_dir.close()
    
    @istest
    def raises_error_if_path_does_not_exist(self):
        assert_raises_regexp(
            IOError,
            "^/not/a/real/path/asljfliahfkb34525: No such file or directory",
            lambda: list(paths.find_files("/not/a/real/path/asljfliahfkb34525")),
        )
        
    @istest
    def returns_path_if_path_references_a_file(self):
        path = self._touch("go.py")
        
        assert_equal([path], list(paths.find_files(path)))
        
    @istest
    def returns_files_in_referenced_directory(self):
        self._mkdir("x")
        path = self._touch("x/go.py")
        
        assert_equal([path], list(paths.find_files(path)))
        
    @istest
    def returns_files_in_subdirectories_of_referenced_directory(self):
        self._mkdir("x")
        self._mkdir("x/y")
        path = self._touch("x/y/go.py")
        
        assert_equal([path], list(paths.find_files(path)))
    
    def _mkdir(self, path):
        os.mkdir(self._temp_path(path))
    
    def _touch(self, path):
        full_path = self._temp_path(path)
        
        with open(full_path, "w") as f:
            f.write("")
        
        return full_path
    
    def _temp_path(self, path):
        return os.path.join(self._temp_dir.path, path)
