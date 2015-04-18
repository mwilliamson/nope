import ast

from .. import nodes as _nodes


def python_to_nope(python_ast, comment_seeker, is_executable, filename=None):
    converter = Converter(comment_seeker, is_executable, filename=filename)
    return converter.convert(python_ast)


class _NodeBuilder(object):
    def __init__(self, location):
        self._location = location
    
    def __getattr__(self, key):
        create_node = getattr(_nodes, key)
        def create_node_with_location(*args, **kwargs):
            node = create_node(*args, **kwargs)
            node.location = self._location
            return node
        
        return create_node_with_location


class _Location(object):
    def __init__(self, filename, lineno, offset):
        self.filename = filename
        self.lineno = lineno
        self.offset = offset


class Converter(object):
    def __init__(self, comment_seeker, is_executable, filename):
        self._comment_seeker = comment_seeker
        self._is_executable = is_executable
        self._filename = filename
        
        self._node_builders = []

        self._converters = {
            ast.Module: self._module,
            
            ast.Import: self._import,
            ast.ImportFrom: self._import_from,
            ast.alias: self._import_alias,
            
            ast.FunctionDef: self._func,
            ast.arguments: self._arguments,
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
            ast.Tuple: self._tuple_literal,
            ast.List: self._list_literal,
            ast.Dict: self._dict_literal,
            ast.Name: self._name,
            ast.Call: self._call,
            ast.Attribute: self._attr,
            ast.BinOp: self._bin_op,
            ast.UnaryOp: self._unary_op,
            ast.Compare: self._compare,
            ast.Subscript: self._subscript,
            ast.Index: self._index,
            ast.Slice: self._slice,
            ast.BoolOp: self._bool_op,
            ast.ListComp: self._list_comprehension,
            ast.GeneratorExp: self._generator_expression,
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
        filename = self._filename
        lineno, col_offset = self._node_location(node)
        
        self._nodes = _NodeBuilder(_Location(filename, lineno, col_offset))
        self._node_builders.append(self._nodes)
        try:
            type_definition = self._comment_seeker.consume_type_definition(lineno, col_offset)
            field_definition = self._comment_seeker.consume_field(lineno, col_offset)
            
            converter = self._converters.get(type(node))
            if converter is None:
                raise SyntaxError("syntax node not supported: {0}".format(type(node).__name__))
                
            nope_node = self._converters[type(node)](node)
            
            if type_definition is not None:
                assert nope_node == self._nodes.assign([self._nodes.ref(type_definition.name)], self._nodes.none())
                nope_node = type_definition
            
            if field_definition is not None:
                # TODO: unwrap string node here
                nope_node = self._nodes.field_definition(nope_node, field_definition)
            
            if allowed is not None and not isinstance(nope_node, allowed):
                raise SyntaxError("{} node is not supported in current context".format(type(nope_node).__name__))
                
            return nope_node
        except SyntaxError as error:
            if error.filename is None:
                error.filename = filename
            if error.lineno is None:
                error.lineno = lineno
            if error.offset is None:
                error.offset = col_offset
            
            raise
        finally:
            self._node_builders.pop()
            if self._node_builders:
                self._nodes = self._node_builders[-1]
            else:
                self._nodes = None
    
    def _node_location(self, node):
        return getattr(node, "lineno", None), getattr(node, "col_offset", None)
    
    def _module(self, node):
        return self._nodes.module(self._statements(node.body), is_executable=self._is_executable)


    def _import(self, node):
        return self._nodes.Import(self._mapped(node.names))


    def _import_from(self, node):
        if node.module == "__future__":
            future_imports = set([
                "nested_scopes",
                "generators",
                "division",
                "absolute_import",
                "with_statement",
                "print_function",
                "unicode_literals",
            ])
            
            for name in node.names:
                if name.name not in future_imports:
                    raise SyntaxError("Unknown __future__ import: '{}'".format(name.name))
            return None
        
        if node.level == 1:
            module_path = ["."]
        else:
            module_path = [".."] * (node.level - 1)
        
        
        if node.module:
            module_path += node.module.split(".")
        
        return self._nodes.import_from(module_path, self._mapped(node.names))
    
    
    def _import_alias(self, node):
        return self._nodes.import_alias(node.name, node.asname)


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
        
        
        signature = self._explicit_type_of(node)
        
        return self._nodes.func(
            name=node.name,
            args=self.convert(node.args),
            body=self._statements(node.body),
            type=signature,
        )
    
    def _arguments(self, node):
        defaults = self._mapped(node.defaults)
        for default in defaults:
            if not isinstance(default, _nodes.NoneLiteral):
                raise SyntaxError("default argument must be None")
        
        arg_defaults = [None] * (len(node.args) - len(defaults)) + defaults
        
        return self._nodes.arguments([
            self._nodes.argument(arg.arg, default is not None)
            for arg, default in zip(node.args, arg_defaults)
        ])


    def _expr(self, node):
        return self._nodes.expression_statement(self.convert(node.value))

    
    def _return(self, node):
        return self._nodes.ret(self._convert_or_none_node(node.value))
    
    
    def _assign(self, node):
        signature = self._explicit_type_of(node)
        
        targets = [self.convert(target) for target in node.targets]
        
        return self._nodes.assign(targets, self.convert(node.value), type=signature)
    
    
    def _if(self, node):
        return self._nodes.if_(
            self.convert(node.test),
            self._statements(node.body),
            self._statements(node.orelse),
        )
    
    
    def _while(self, node):
        return self._nodes.while_(
            self.convert(node.test),
            self._statements(node.body),
            self._statements(node.orelse),
        )
    
    
    def _for(self, node):
        return self._nodes.for_(
            self.convert(node.target),
            self.convert(node.iter),
            self._statements(node.body),
            self._statements(node.orelse),
        )
    
    
    def _break(self, node):
        return self._nodes.break_()
    
    
    def _continue(self, node):
        return self._nodes.continue_()
    
    
    def _try(self, node):
        if getattr(node, "orelse", None):
            raise SyntaxError("'else' clause in 'try' statement is unsupported")
        
        return self._nodes.try_(
            self._statements(node.body),
            handlers=self._mapped(getattr(node, "handlers", [])),
            finally_body=self._statements(getattr(node, "finalbody", [])),
        )
    
    
    def _except(self, node):
        if node.type is None:
            type_ = None
        else:
            type_ = self.convert(node.type)
            
        return self._nodes.except_(
            type_,
            node.name,
            self._statements(node.body),
        )
    
    
    def _raise(self, node):
        return self._nodes.raise_(self.convert(node.exc))
    
    
    def _assert(self, node):
        condition = self.convert(node.test)
        if node.msg is None:
            message = None
        else:
            message = self.convert(node.msg)
        return self._nodes.assert_(condition, message)


    def _with(self, node):
        result = self._statements(node.body)
        
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
            
            result = [self._nodes.with_(
                self.convert(item.context_expr),
                target,
                result,
            )]
        
        return result[0]
    
    
    def _class_def(self, node):
        if node.starargs:
            raise SyntaxError("base classes in the form '*{}' are not supported".format(node.starargs.id))
        if node.keywords or node.kwargs:
            raise SyntaxError("class keyword arguments are not supported")
        if node.decorator_list:
            raise SyntaxError("class decorators are not supported")
        
        body = self._statements(node.body, allowed=(_nodes.Assignment, _nodes.FunctionDef))
        base_classes = self._mapped(node.bases)
        lineno, col_offset = self._node_location(node)
        generics = self._comment_seeker.consume_generic(lineno, col_offset)
        return self._nodes.class_(node.name, body, base_classes=base_classes, type_params=generics)
    

    def _str_literal(self, node):
        return self._nodes.str_literal(node.s)


    def _num_literal(self, node):
        value = node.n
        if isinstance(value, int):
            return self._nodes.int_literal(value)
    
    
    def _tuple_literal(self, node):
        return self._nodes.tuple_literal(self._mapped(node.elts))
    
    
    def _list_literal(self, node):
        return self._nodes.list_literal(self._mapped(node.elts))


    def _dict_literal(self, node):
        return self._nodes.dict_literal(list(zip(self._mapped(node.keys), self._mapped(node.values))))


    def _name(self, node):
        if node.id == "None":
            return self._nodes.none()
        elif node.id == "True":
            return self._nodes.bool_literal(True)
        elif node.id == "False":
            return self._nodes.bool_literal(False)
        else:
            return self._nodes.ref(node.id)
    
    
    def _name_constant(self, node):
        if node.value is None:
            return self._nodes.none()
        elif isinstance(node.value, bool):
            return self._nodes.bool_literal(node.value)
        else:
            raise ValueError("Unrecognised constant: {}".format(node.value))
    

    def _call(self, node):
        return self._nodes.call(
            self.convert(node.func),
            self._mapped(node.args),
            dict(
                (keyword.arg, self.convert(keyword.value))
                for keyword in node.keywords
            ),
        )
    
    
    def _attr(self, node):
        return self._nodes.attr(self.convert(node.value), node.attr)
    
    
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
                compare_node = self._nodes.bool_and(compare_node, comparison)
            
        return compare_node
    
    def _create_comparison(self, op, left, right):
        if isinstance(op, ast.In):
            left, right = right, left
        return self._operator(op)(self.convert(left), self.convert(right))
    
    def _operator(self, operator):
        operators = {
            ast.Add: self._nodes.add,
            ast.Sub: self._nodes.sub,
            ast.Mult: self._nodes.mul,
            ast.Div: self._nodes.truediv,
            ast.FloorDiv: self._nodes.floordiv,
            ast.Mod: self._nodes.mod,
            ast.Pow: self._nodes.pow,
            ast.LShift: self._nodes.lshift,
            ast.RShift: self._nodes.rshift,
            ast.BitAnd: self._nodes.and_,
            ast.BitOr: self._nodes.or_,
            ast.BitXor: self._nodes.xor_,
            
            ast.USub: self._nodes.neg,
            ast.UAdd: self._nodes.pos,
            ast.Invert: self._nodes.invert,
            
            ast.Eq: self._nodes.eq,
            ast.NotEq: self._nodes.ne,
            ast.Lt: self._nodes.lt,
            ast.LtE: self._nodes.le,
            ast.Gt: self._nodes.gt,
            ast.GtE: self._nodes.ge,
            
            ast.And: self._nodes.bool_and,
            ast.Or: self._nodes.bool_or,
            ast.Not: self._nodes.bool_not,
            
            ast.Is: self._nodes.is_,
            ast.IsNot: self._nodes.is_not,
            
            ast.In: self._nodes.contains,
        }
        return operators[type(operator)]
    
    def _subscript(self, node):
        return self._nodes.subscript(self.convert(node.value), self.convert(node.slice))
    
    def _index(self, node):
        return self.convert(node.value)
    
    def _slice(self, node):
        return self._nodes.slice(
            self._convert_or_none_node(node.lower),
            self._convert_or_none_node(node.upper),
            self._convert_or_none_node(node.step),
        )

    def _bool_op(self, node):
        values = [self.convert(value) for value in node.values]
        create_node = self._operator(node.op)
        
        node = create_node(values[0], values[1])
        for value in values[2:]:
            node = create_node(node, value)
        return node
    
    def _list_comprehension(self, node):
        return self._comprehension(self._nodes.list_comprehension, node)
    
    def _generator_expression(self, node):
        return self._comprehension(self._nodes.generator_expression, node)
    
    def _comprehension(self, create, node):
        # TODO: support nested fors
        generator, = node.generators
        # TODO: support ifs
        assert not generator.ifs
        
        return create(self.convert(node.elt), self.convert(generator.target), self.convert(generator.iter))


    def _explicit_type_of(self, node):
        return self._comment_seeker.consume_explicit_type(*(self._node_location(node)))

    def _mapped(self, nodes, allowed=None):
        return list(filter(None, (
            self.convert(node, allowed=allowed)
            for node in nodes
            if not isinstance(node, ast.Pass)
        )))
    
    _statements = _mapped
    
    def _convert_or_none_node(self, node):
        return self._convert_or_default(node, self._nodes.none)
    
    def _convert_or_default(self, node, default):
        if node is None:
            return default()
        else:
            return self.convert(node)
