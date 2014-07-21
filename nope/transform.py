import ast

from . import nodes


def python_to_nope(python_ast, comment_seeker):
    converter = Converter(comment_seeker)
    return converter.convert(python_ast)

class Converter(object):
    def __init__(self, comment_seeker):
        self._comment_seeker = comment_seeker

        self._converters = {
            ast.Module: self._module,
            ast.FunctionDef: self._func,
            ast.Expr: self._expr,
            ast.Return: self._return,
            
            ast.Str: self._str_literal,
            ast.Num: self._num_literal,
            ast.Name: self._name,
            ast.Call: self._call,
        }


    
    def convert(self, node):
        return self._converters[type(node)](node)
    
    def _module(self, node):
        return nodes.module(self._mapped(node.body))


    def _func(self, node):
        signature = self._comment_seeker.seek_signature(node.lineno, node.col_offset)
        if signature is None:
            type_params = []
            
            arg_annotations = [
                self.convert(arg.annotation)
                for arg in node.args.args
            ]
            
            if node.returns is None:
                return_annotation = None
            else:
                return_annotation = self.convert(node.returns)
        else:
            type_params, arg_annotations, return_annotation = signature
        
        def _arg(node, annotation):
            return nodes.argument(node.arg, annotation)
        
        if len(node.args.args) != len(arg_annotations):
            raise SyntaxError("args length mismatch: def has {0}, signature has {1}".format(
                len(node.args.args), len(arg_annotations)))
        
        args = nodes.arguments(list(map(_arg, node.args.args, arg_annotations)))
        
        
        return nodes.func(
            name=node.name,
            args=args,
            return_annotation=return_annotation,
            body=self._mapped(node.body),
            type_params=type_params,
        )


    def _expr(self, node):
        return nodes.expression_statement(self.convert(node.value))

    
    def _return(self, node):
        return nodes.ret(self.convert(node.value))
    

    def _str_literal(self, node):
        return nodes.str(node.s)


    def _num_literal(self, node):
        value = node.n
        if isinstance(value, int):
            return nodes.int(value)


    def _name(self, node):
        return nodes.ref(node.id)


    def _call(self, node):
        return nodes.call(self.convert(node.func), self._mapped(node.args))


    def _mapped(self, nodes):
        return [
            self.convert(node)
            for node in nodes
            if not isinstance(node, ast.Pass)
        ]
