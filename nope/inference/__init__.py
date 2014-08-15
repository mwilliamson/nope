import os

from .. import types, nodes, util, errors, returns
from ..context import new_module_context
from .expressions import ExpressionTypeInferer
from .statements import StatementTypeChecker


def check(module, source_tree=None, module_path=None):
    checker = _TypeChecker(source_tree, module_path, module.is_executable)
    module_type = checker.check(module)
    return module_type, checker.type_lookup()

def infer(expression, context, source_tree=None, module_path=None):
    checker = _TypeChecker(source_tree, module_path, False)
    return checker.infer(expression, context)

def update_context(statement, context, source_tree=None, module_path=None, is_executable=False):
    checker = _TypeChecker(source_tree, module_path, is_executable)
    return checker.update_context(statement, context)


class _TypeChecker(object):
    def __init__(self, source_tree, module_path, is_executable):
        self._source_tree = source_tree
        self._module_path = module_path
        self._type_lookup = {}
        self._expression_type_inferer = ExpressionTypeInferer(self._type_lookup)
        self._statement_type_checker = StatementTypeChecker(self._expression_type_inferer, source_tree, module_path, is_executable)
    
    def type_lookup(self):
        return types.TypeLookup(self._type_lookup)
    
    def infer(self, expression, context):
        return self._expression_type_inferer.infer(expression, context)

    def update_context(self, statement, context):
        self._statement_type_checker.update_context(statement, context)

    def check(self, module):
        context = new_module_context(util.declared_locals(module.body))
        for statement in module.body:
            self.update_context(statement, context)
        
        return types.Module(self._module_path, dict(
            (name, context.lookup(name))
            for name in util.exported_names(module)
            if context.is_bound(name)
        ))
        


    
