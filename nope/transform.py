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
            ast.While: self._while,
            ast.For: self._for,
            ast.Break: self._break,
            ast.Continue: self._continue,
            ast.ExceptHandler: self._except,
            ast.Raise: self._raise,
            ast.Assert: self._assert,
            ast.With: self._with,
            
            ast.Str: self._str_literal,
            ast.Num: self._num_literal,
            ast.List: self._list_literal,
            ast.Name: self._name,
            ast.Call: self._call,
            ast.Attribute: self._attr,
            ast.BinOp: self._bin_op,
            ast.UnaryOp: self._unary_op,
            ast.Subscript: self._subscript,
            ast.Index: self._index,
        }
        
        # Python >= 3.3:
        if hasattr(ast, "Try"):
            self._converters[ast.Try] = self._try
        
        # Python < 3.3
        if hasattr(ast, "TryExcept"):
            self._converters[ast.TryExcept] = self._try
        if hasattr(ast, "TryFinally"):
            self._converters[ast.TryFinally] = self._try
        
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
            signature = nodes.signature(type_params=[], args=[], returns=None)
        
        if node.args.kwonlyargs:
            raise SyntaxError("keyword-only arguments are not supported")
        
        if node.args.vararg is not None:
            raise SyntaxError("arguments in the form '*{}' are not supported".format(node.args.vararg.arg))
        
        if node.args.kwarg is not None:
            raise SyntaxError("arguments in the form '**{}' are not supported".format(node.args.kwarg.arg))
        
        if len(node.args.args) != len(signature.args):
            raise SyntaxError("args length mismatch: def has {0}, signature has {1}".format(
                len(node.args.args), len(signature.args)))
        
        for def_arg, signature_arg in zip(node.args.args, signature.args):
            if signature_arg.name is not None and def_arg.arg != signature_arg.name:
                raise SyntaxError("argument '{}' has name '{}' in signature".format(def_arg.arg, signature_arg.name))
        
        args = nodes.arguments([
            nodes.argument(arg.arg)
            for arg in node.args.args
        ])
        
        return nodes.func(
            name=node.name,
            signature=signature,
            args=args,
            body=self._mapped(node.body),
        )


    def _expr(self, node):
        return nodes.expression_statement(self.convert(node.value))

    
    def _return(self, node):
        if node.value is None:
            value = nodes.none()
        else:
            value = self.convert(node.value)
        return nodes.ret(value)
    
    
    def _assign(self, node):
        targets = [self.convert(target) for target in node.targets]
        
        return nodes.assign(targets, self.convert(node.value))
    
    
    def _if(self, node):
        return nodes.if_else(
            self.convert(node.test),
            self._mapped(node.body),
            self._mapped(node.orelse),
        )
    
    
    def _while(self, node):
        return nodes.while_loop(
            self.convert(node.test),
            self._mapped(node.body),
            self._mapped(node.orelse),
        )
    
    
    def _for(self, node):
        return nodes.for_loop(
            self.convert(node.target),
            self.convert(node.iter),
            self._mapped(node.body),
            self._mapped(node.orelse),
        )
    
    
    def _break(self, node):
        return nodes.break_statement()
    
    
    def _continue(self, node):
        return nodes.continue_statement()
    
    
    def _try(self, node):
        if node.orelse:
            raise SyntaxError("'else' clause in 'try' statement is unsupported")
        
        return nodes.try_statement(
            self._mapped(node.body),
            handlers=self._mapped(getattr(node, "handlers", [])),
            finally_body=self._mapped(getattr(node, "finalbody", [])),
        )
    
    
    def _except(self, node):
        if node.type is None:
            type_ = None
        else:
            type_ = self.convert(node.type)
            
        return nodes.except_handler(
            type_,
            node.name,
            self._mapped(node.body),
        )
    
    
    def _raise(self, node):
        return nodes.raise_statement(self.convert(node.exc))
    
    
    def _assert(self, node):
        condition = self.convert(node.test)
        if node.msg is None:
            message = None
        else:
            message = self.convert(node.msg)
        return nodes.assert_statement(condition, message)


    def _with(self, node):
        result = self._mapped(node.body)
        
        if hasattr(node, "items"):
            # Python >= 3.3
            items = reversed(node.items)
        else:
            items = [node]
        
        for item in items:
            if item.optional_vars is None:
                target = None
            else:
                target = self.convert(item.optional_vars)
            
            result = [nodes.with_statement(
                self.convert(item.context_expr),
                target,
                result,
            )]
        
        return result[0]
    

    def _str_literal(self, node):
        return nodes.string(node.s)


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
        return nodes.call(
            self.convert(node.func),
            self._mapped(node.args),
            dict(
                (keyword.arg, self.convert(keyword.value))
                for keyword in node.keywords
            ),
        )
    
    
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
            ast.Pow: nodes.pow,
            ast.LShift: nodes.lshift,
            ast.RShift: nodes.rshift,
            ast.BitAnd: nodes.and_,
            ast.BitOr: nodes.or_,
            ast.BitXor: nodes.xor_,
            
            ast.USub: nodes.neg,
            ast.UAdd: nodes.pos,
            ast.Invert: nodes.invert,
        }
        return operators[type(operator)]
    
    def _subscript(self, node):
        return nodes.subscript(self.convert(node.value), self.convert(node.slice))
    
    def _index(self, node):
        return self.convert(node.value)

    def _mapped(self, nodes):
        return [
            self.convert(node)
            for node in nodes
            if not isinstance(node, ast.Pass)
        ]
