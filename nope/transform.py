import ast

from . import nodes


def python_to_nope(python_ast, comment_seeker, is_executable, filename=None):
    converter = Converter(comment_seeker, is_executable, filename=filename)
    return converter.convert(python_ast)

class Converter(object):
    def __init__(self, comment_seeker, is_executable, filename):
        self._comment_seeker = comment_seeker
        self._is_executable = is_executable
        self._filename = filename

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
            ast.ClassDef: self._class_def,
            
            ast.Str: self._str_literal,
            ast.Num: self._num_literal,
            ast.List: self._list_literal,
            ast.Name: self._name,
            ast.Call: self._call,
            ast.Attribute: self._attr,
            ast.BinOp: self._bin_op,
            ast.UnaryOp: self._unary_op,
            ast.Compare: self._compare,
            ast.Subscript: self._subscript,
            ast.Index: self._index,
            ast.BoolOp: self._bool_op,
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

    
    def convert(self, node, allowed=None):
        try:
            nope_node = self._converters[type(node)](node)
            if allowed is not None and not isinstance(nope_node, allowed):
                raise SyntaxError("{} node is not supported in current context".format(type(nope_node).__name__))
        except SyntaxError as error:
            if error.lineno is None:
                error.lineno = node.lineno
            if error.offset is None:
                error.offset = node.col_offset
            
            raise
        
        if hasattr(node, "lineno"):
            nope_node.lineno = node.lineno
        if hasattr(node, "col_offset"):
            nope_node.offset = node.col_offset
            
        nope_node.filename = self._filename
        
        return nope_node
    
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
        if node.decorator_list:
            raise SyntaxError("function decorators are not supported")
        
        if node.args.kwonlyargs:
            raise SyntaxError("keyword-only arguments are not supported")
        
        if node.args.vararg is not None:
            # vararg changed from identifier? to arg? in Python 3.4
            name = getattr(node.args.vararg, "arg", node.args.vararg)
            raise SyntaxError("arguments in the form '*{}' are not supported".format(name))
        
        if node.args.kwarg is not None:
            # kwarg changed from identifier? to arg? in Python 3.4
            name = getattr(node.args.kwarg, "arg", node.args.kwarg)
            raise SyntaxError("arguments in the form '**{}' are not supported".format(name))
        
        
        signature = self._comment_seeker.seek_signature(node.lineno, node.col_offset)
        if signature is None:
            if len(node.args.args) == 0:
                signature = nodes.signature(type_params=[], args=[], returns=None)
            else:
                raise SyntaxError("signature is missing from function definition")
        
        
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
        if getattr(node, "orelse", None):
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
    
    
    def _class_def(self, node):
        if node.bases or node.starargs:
            raise SyntaxError("base classes are not supported")
        if node.keywords or node.kwargs:
            raise SyntaxError("class keyword arguments are not supported")
        if node.decorator_list:
            raise SyntaxError("class decorators are not supported")
            
        return nodes.class_def(node.name, self._mapped(node.body, allowed=(nodes.Assignment, nodes.FunctionDef)))
    

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
    
    
    def _compare(self, node):
        operands = [node.left] + node.comparators
        compare_node = None
        
        for op, left, right in zip(node.ops, operands, operands[1:]):
            comparison = self._create_comparison(op, left, right)
            if compare_node is None:
                compare_node = comparison
            else:
                compare_node = nodes.bool_and(compare_node, comparison)
            
        return compare_node
    
    def _create_comparison(self, op, left, right):
        return self._operator(op)(self.convert(left), self.convert(right))
    
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
            
            ast.Eq: nodes.eq,
            ast.NotEq: nodes.ne,
            ast.Lt: nodes.lt,
            ast.LtE: nodes.le,
            ast.Gt: nodes.gt,
            ast.GtE: nodes.ge,
            
            ast.And: nodes.bool_and,
            ast.Or: nodes.bool_or,
            ast.Not: nodes.bool_not,
            
            ast.Is: nodes.is_,
        }
        return operators[type(operator)]
    
    def _subscript(self, node):
        return nodes.subscript(self.convert(node.value), self.convert(node.slice))
    
    def _index(self, node):
        return self.convert(node.value)

    def _bool_op(self, node):
        values = [self.convert(value) for value in node.values]
        create_node = self._operator(node.op)
        
        node = create_node(values[0], values[1])
        for value in values[2:]:
            node = create_node(node, value)
        return node

    def _mapped(self, nodes, allowed=None):
        return [
            self.convert(node, allowed=allowed)
            for node in nodes
            if not isinstance(node, ast.Pass)
        ]
