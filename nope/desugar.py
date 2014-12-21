import itertools

from . import nodes, visit
from .modules import LocalModule


def desugar(module):
    if not isinstance(module, LocalModule):
        raise Exception("Unhandled desugar type: {}".format(module))
    
    visitor = visit.Visitor()
    visitor.replace(nodes.WithStatement, _with_statement)
    
    return LocalModule(module.path, visitor.visit(module.node))
    

def _with_statement(visitor, statement):
    exception_name = _generate_unique_name("exception")
    manager_name = _generate_unique_name("manager")
    exit_method_var_name = _generate_unique_name("exit")
    has_exited_name = _generate_unique_name("has_exited")
    
    manager_ref = lambda: nodes.ref(manager_name)
    
    enter_value = nodes.call(_get_magic_method(manager_ref(), "enter"), [])
    if statement.target is None:
        enter_statement = nodes.expression_statement(enter_value)
    else:
        enter_statement = nodes.assign([statement.target], enter_value)
    
    return nodes.Statements([
        nodes.assign([manager_ref()], statement.value),
        nodes.assign([nodes.ref(exit_method_var_name)], _get_magic_method(manager_ref(), "exit")),
        nodes.assign([nodes.ref(has_exited_name)], nodes.boolean(False)),
        enter_statement,
        nodes.try_statement(
            statement.body,
            handlers=[nodes.except_handler(_builtin_ref("Exception"), nodes.ref(exception_name), [
                nodes.assign([nodes.ref(has_exited_name)], nodes.boolean(True)),
                nodes.if_else(
                    nodes.bool_not(nodes.call(nodes.ref(exit_method_var_name), [
                        nodes.call(_builtin_ref("type"), [nodes.ref(exception_name)]),
                        nodes.ref(exception_name),
                        nodes.none(),
                    ])),
                    [nodes.raise_statement(nodes.ref(exception_name))],
                    [],
                ),
                
            ])],
            finally_body=[
                nodes.if_else(
                    nodes.bool_not(nodes.ref(has_exited_name)),
                    [
                        nodes.expression_statement(nodes.call(
                            nodes.ref(exit_method_var_name),
                            [nodes.none(), nodes.none(), nodes.none()]
                        )),
                    ],
                    [],
                ),
            ],
        ),
    ])


def _get_magic_method(receiver, name):
    # TODO: get magic method through the same mechanism as self._call
    return nodes.attr(receiver, "__{}__".format(name))

def _builtin_ref(name):
    # TODO: create a distinct node type for referring to builtins
    return nodes.ref(name)


_unique_count = itertools.count()

def _generate_unique_name(name):
    return "____nope_{}__".format(name, next(_unique_count))
