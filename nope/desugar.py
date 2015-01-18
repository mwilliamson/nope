import itertools

from . import nodes, visit, couscous as cc, modules
from .modules import LocalModule


def desugar(node):
    desugarrer = Desugarrer()
    return desugarrer.desugar(node)


class Desugarrer(object):
    def __init__(self):
        self._unique_count = itertools.count()
    
        self._transforms = {
            LocalModule: self._local_module,
            
            nodes.Module: self._module,
        
            nodes.WithStatement: self._with_statement,
            
            nodes.ReturnStatement: self._return,
            nodes.ExpressionStatement: self._expression_statement,
            
            nodes.VariableReference: self._ref,
            list: lambda nope_nodes: list(map(self.desugar, nope_nodes)),
        }
    
    def desugar(self, node):
        return self._transforms[type(node)](node)
        
    def _local_module(self, module):
        return LocalModule(module.path, self.desugar(module.node))
    
    def _module(self, module):
        return cc.module(self.desugar(module.body), is_executable=module.is_executable)
    
    def _with_statement(self, statement):
        exception_name = self._generate_unique_name("exception")
        manager_name = self._generate_unique_name("manager")
        exit_method_var_name = self._generate_unique_name("exit")
        has_exited_name = self._generate_unique_name("has_exited")
        
        manager_ref = cc.ref(manager_name)
        
        enter_value = cc.call(self._get_magic_method(manager_ref, "enter"), [])
        if statement.target is None:
            enter_statement = cc.expression_statement(enter_value)
        else:
            enter_statement = cc.assign(self.desugar(statement.target), enter_value)
        
        return cc.statements([
            cc.assign(manager_ref, self.desugar(statement.value)),
            cc.assign(cc.ref(exit_method_var_name), self._get_magic_method(manager_ref, "exit")),
            cc.assign(cc.ref(has_exited_name), cc.false),
            enter_statement,
            cc.try_(
                desugar(statement.body),
                handlers=[cc.except_(self._builtin_ref("Exception"), cc.ref(exception_name), [
                    cc.assign(cc.ref(has_exited_name), cc.true),
                    cc.if_(
                        cc.not_(_bool(cc.call(cc.ref(exit_method_var_name), [
                            cc.call(self._builtin_ref("type"), [cc.ref(exception_name)]),
                            cc.ref(exception_name),
                            cc.none,
                        ]))),
                        [cc.raise_()],
                        [],
                    ),
                    
                ])],
                finally_body=[
                    cc.if_(
                        cc.not_(cc.ref(has_exited_name)),
                        [
                            cc.expression_statement(cc.call(
                                cc.ref(exit_method_var_name),
                                [cc.none, cc.none, cc.none]
                            )),
                        ],
                        [],
                    ),
                ],
            ),
        ])
    
    def _return(self, node):
        return cc.ret(self.desugar(node.value))
    
    def _expression_statement(self, node):
        return cc.expression_statement(self.desugar(node.value))
    
    def _ref(self, node):
        return cc.ref(node.name)


    def _get_magic_method(self, receiver, name):
        # TODO: get magic method through the same mechanism as self._call
        return cc.attr(receiver, "__{}__".format(name))

    def _builtin_ref(self, name):
        return cc.builtin(name)

    def _generate_unique_name(self, name):
        return "${}{}".format(name, next(self._unique_count))

def _bool(value):
    return cc.call(cc.builtin("bool"), [value])
