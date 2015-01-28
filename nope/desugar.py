import itertools

import zuice

from . import nodes, visit, couscous as cc, types
from .name_declaration import DeclarationFinder
from .modules import LocalModule


def desugar(node, type_lookup, declarations):
    desugarrer = Desugarrer(type_lookup, declarations)
    return desugarrer.desugar(node)


class Desugarrer(zuice.Base):
    _type_lookup = zuice.dependency(types.TypeLookup)
    _declarations = zuice.dependency(DeclarationFinder)
    
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
            nodes.AttributeAccess: self._attr,
            nodes.VariableReference: self._ref,
            nodes.StringLiteral: self._str,
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
            for attr in self._type_of(module).attrs
        ]
        
        declared_names = set(self._declarations.declarations_in_module(module).names())
        declarations = list(map(cc.declare, sorted(declared_names)))
        
        return cc.module(
            declarations + self.desugar(module.body),
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
            cc.declare(manager_name, self.desugar(statement.value)),
            cc.declare(exit_method_var_name, self._get_magic_method(manager_ref, "exit")),
            cc.declare(has_exited_name, cc.false),
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
        declared_names = set(self._declarations.declarations_in_function(node).names())
        arg_names = [arg.name for arg in node.args.args]
        declared_names.difference_update(arg_names)
        declarations = list(map(cc.declare, sorted(declared_names)))
        
        return cc.func(node.name, self.desugar(node.args), declarations + self.desugar(node.body))
    
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
        # TODO: proper support for __call__
        # at the moment, we only support meta-types that are directly callable e.g. str()
        # a better solution might be have such values have a $call attribute (or similar)
        # to avoid clashing with actual __call__ attributes
        args = []
        
        call_func_type = self._type_of(node.func)
        call_ref = node.func
        while not types.is_func_type(call_func_type) and not types.is_generic_func(call_func_type):
            call_func_type = call_func_type.attrs.type_of("__call__")
            call_ref = nodes.attr(call_ref, "__call__")
        
        for index, formal_arg in enumerate(call_func_type.args):
            if index < len(node.args):
                actual_arg_node = node.args[index]
            elif formal_arg.name in node.kwargs:
                actual_arg_node = node.kwargs[formal_arg.name]
            else:
                actual_arg_node = nodes.none()
                
            args.append(self.desugar(actual_arg_node))
            
        return cc.call(self.desugar(call_ref), args)
    
    def _attr(self, node):
        return cc.attr(self.desugar(node.value), node.attr)
    
    def _ref(self, node):
        return cc.ref(node.name)
    
    def _str(self, node):
        return cc.str_literal(node.value)
    
    def _int(self, node):
        return cc.int_literal(node.value)
    
    def _none(self, node):
        return cc.none

    
    def _type_of(self, node):
        return self._type_lookup.type_of(node)
    
    def _get_magic_method(self, receiver, name):
        # TODO: get magic method through the same mechanism as self._call
        return cc.attr(receiver, "__{}__".format(name))

    def _builtin_ref(self, name):
        return cc.builtin(name)

    def _generate_unique_name(self, name):
        return "${}{}".format(name, next(self._unique_count))

def _bool(value):
    return cc.call(cc.builtin("bool"), [value])
