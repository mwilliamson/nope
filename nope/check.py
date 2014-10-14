from . import loop_control


class ModuleChecker(object):
    def __init__(self, source_tree, type_checker):
        self._source_tree = source_tree
        self._type_checker = type_checker
        self._check_results = {}
    
    def check(self, module):
        self._check_result(module)
    
    def _check_result(self, module):
        # TODO: circular import detection
        if module not in self._check_results:
            self._check_results[module] = self._uncached_check(module)
        return self._check_results[module]
    
    def type_of_module(self, module):
        module_type, type_lookup = self._check_result(module)
        return module_type
    
    def type_lookup(self, module):
        module_type, type_lookup = self._check_result(module) 
        return type_lookup
    
    def _uncached_check(self, module):
        loop_control.check_loop_control(module.node, in_loop=False)
        return self._type_checker.check_module(module, self)
