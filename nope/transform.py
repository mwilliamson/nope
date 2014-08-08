import ast

from . import nodes


def python_to_nope(python_ast, comment_seeker, is_executable):
    converter = Converter(comment_seeker, is_executable)
    return converter.convert(python_ast)

class Converter(object):
    def __init__(self, comment_seeker, is_executable):
        self._comment_seeker = comment_seeker
        self._is_executable = is_executable

        self._converters = {
            ast.Module: self._module,
            
            ast.Import: self._import,
            ast.ImportFrom: self._import_from,
            ast.alias: self._import_alias,
            
            ast.FunctionDef: self._func,
            ast.Expr: self._expr,
            ast.Return: self._return,
            ast.Assign: self._assign,
            ast.If: self._if,
            
            ast.Str: self._str_literal,
            ast.Num: self._num_literal,
            ast.List: self._list_literal,
            ast.Name: self._name,
            ast.Call: self._call,
            ast.Attribute: self._attr,
            ast.BinOp: self._bin_op,
            ast.UnaryOp: self._unary_op,
        }
        
        # Python >= 3.4 has ast.NameConstant instead of reusing ast.Name
        if hasattr(ast, "NameConstant"):
            self._converters[ast.NameConstant] = self._name_constant

    
    def convert(self, node):
        return self._converters[type(node)](node)
    
    def _module(self, node):
        return nodes.module(self._mapped(node.body), is_executable=self._is_executable)


    def _import(self, node):
        return nodes.Import(self._mapped(node.names))


    def _import_from(self, node):
        if node.level == 1:
            module_path = ["."]
        else:
            module_path = [".."] * (node.level - 1)
        
        
        if node.module:
            module_path += node.module.split(".")
        
        return nodes.import_from(module_path, self._mapped(node.names))
    
    
    def _import_alias(self, node):
        return nodes.import_alias(node.name, node.asname)


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
    
    
    def _assign(self, node):
        def extract_id(name):
            assert isinstance(name, ast.Name)
            return name.id
        
        names = [extract_id(target) for target in node.targets]
        
        return nodes.assign(names, self.convert(node.value))
    
    
    def _if(self, node):
        return nodes.if_else(
            self.convert(node.test),
            self._mapped(node.body),
            self._mapped(node.orelse),
        )
    

    def _str_literal(self, node):
        return nodes.str(node.s)


    def _num_literal(self, node):
        value = node.n
        if isinstance(value, int):
            return nodes.int(value)
    
    
    def _list_literal(self, node):
        return nodes.list(self._mapped(node.elts))


    def _name(self, node):
        if node.id == "None":
            return nodes.none()
        elif node.id == "True":
            return nodes.boolean(True)
        elif node.id == "False":
            return nodes.boolean(False)
        else:
            return nodes.ref(node.id)
    
    
    def _name_constant(self, node):
        if node.value is None:
            return nodes.none()
        elif isinstance(node.value, bool):
            return nodes.boolean(node.value)
        else:
            raise ValueError("Unrecognised constant: {}".format(node.value))
    

    def _call(self, node):
        return nodes.call(self.convert(node.func), self._mapped(node.args))
    
    
    def _attr(self, node):
        return nodes.attr(self.convert(node.value), node.attr)
    
    
    def _bin_op(self, node):
        return self._operator(node.op)(self.convert(node.left), self.convert(node.right))
    
    
    def _unary_op(self, node):
        return self._operator(node.op)(self.convert(node.operand))
    
    def _operator(self, operator):
        operators = {
            ast.Add: nodes.add,
            ast.Sub: nodes.sub,
            ast.Mult: nodes.mul,
            ast.Div: nodes.truediv,
            ast.FloorDiv: nodes.floordiv,
            ast.Mod: nodes.mod,
            
            ast.USub: nodes.neg,
        }
        return operators[type(operator)]
    

    def _mapped(self, nodes):
        return [
            self.convert(node)
            for node in nodes
            if not isinstance(node, ast.Pass)
        ]
