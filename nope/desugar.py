import itertools

import zuice

from . import nodes, visit, couscous as cc, types
from .modules import LocalModule


def desugar(node, type_lookup):
    desugarrer = Desugarrer(type_lookup)
    return desugarrer.desugar(node)


class Desugarrer(zuice.Base):
    _type_lookup = zuice.dependency(types.TypeLookup)
    
    @zuice.init
    def init(self):
        self._unique_count = itertools.count()
    
        self._transforms = {
            LocalModule: self._local_module,
            
            nodes.Module: self._module,
        
            nodes.WithStatement: self._with_statement,
            nodes.FunctionDef: self._function_definition,
            nodes.Arguments: self._arguments,
            nodes.Argument: self._argument,
            
            nodes.ReturnStatement: self._return,
            nodes.Assignment: self._assignment,
            nodes.ExpressionStatement: self._expression_statement,
            
            nodes.Call: self._call,
            nodes.VariableReference: self._ref,
            nodes.IntLiteral: self._int,
            nodes.NoneLiteral: self._none,
            list: lambda nope_nodes: list(map(self.desugar, nope_nodes)),
        }
    
    def desugar(self, node):
        return self._transforms[type(node)](node)
        
    def _local_module(self, module):
        return LocalModule(module.path, self.desugar(module.node))
    
    def _module(self, module):
        exported_names = [
            attr.name
            for attr in self._type_lookup.type_of(module).attrs
        ]
        
        return cc.module(
            self.desugar(module.body),
            is_executable=module.is_executable,
            exported_names=exported_names
        )
    
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
                self.desugar(statement.body),
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
    
    def _function_definition(self, node):
        return cc.func(node.name, self.desugar(node.args), self.desugar(node.body))
    
    def _arguments(self, node):
        return self.desugar(node.args)
        
    def _argument(self, node):
        return cc.arg(node.name)
    
    def _return(self, node):
        return cc.ret(self.desugar(node.value))
    
    def _assignment(self, node):
        target, = node.targets
        return cc.assign(self.desugar(target), self.desugar(node.value))
    
    def _expression_statement(self, node):
        return cc.expression_statement(self.desugar(node.value))
    
    def _call(self, node):
        return cc.call(self.desugar(node.func), self.desugar(node.args))
    
    def _ref(self, node):
        return cc.ref(node.name)
    
    def _int(self, node):
        return cc.int_literal(node.value)
    
    def _none(self, node):
        return cc.none


    def _get_magic_method(self, receiver, name):
        # TODO: get magic method through the same mechanism as self._call
        return cc.attr(receiver, "__{}__".format(name))

    def _builtin_ref(self, name):
        return cc.builtin(name)

    def _generate_unique_name(self, name):
        return "${}{}".format(name, next(self._unique_count))

def _bool(value):
    return cc.call(cc.builtin("bool"), [value])
