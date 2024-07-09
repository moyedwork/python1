import ast
import builtins
import copy
import dis
import enum
import os
import re
import sys
import textwrap
import types
import unittest
import weakref
from textwrap import dedent
try:
    import _testinternalcapi
except ImportError:
    _testinternalcapi = None

from test import support
from test.support import os_helper, script_helper
from test.support.ast_helper import ASTTestMixin

def to_tuple(t):
    if t is None or isinstance(t, (str, int, complex, float, bytes)) or t is Ellipsis:
        return t
    elif isinstance(t, list):
        return [to_tuple(e) for e in t]
    result = [t.__class__.__name__]
    if hasattr(t, 'lineno') and hasattr(t, 'col_offset'):
        result.append((t.lineno, t.col_offset))
        if hasattr(t, 'end_lineno') and hasattr(t, 'end_col_offset'):
            result[-1] += (t.end_lineno, t.end_col_offset)
    if t._fields is None:
        return tuple(result)
    for f in t._fields:
        result.append(to_tuple(getattr(t, f)))
    return tuple(result)

STDLIB = os.path.dirname(ast.__file__)
STDLIB_FILES = [fn for fn in os.listdir(STDLIB) if fn.endswith(".py")]
STDLIB_FILES.extend(["test/test_grammar.py", "test/test_unpack_ex.py"])

# These tests are compiled through "exec"
# There should be at least one test per statement
exec_tests = [
    # Module docstring
    "'module docstring'",
    # FunctionDef
    "def f(): pass",
    # FunctionDef with docstring
    "def f(): 'function docstring'",
    # FunctionDef with arg
    "def f(a): pass",
    # FunctionDef with arg and default value
    "def f(a=0): pass",
    # FunctionDef with varargs
    "def f(*args): pass",
    # FunctionDef with varargs as TypeVarTuple
    "def f(*args: *Ts): pass",
    # FunctionDef with varargs as unpacked Tuple
    "def f(*args: *tuple[int, ...]): pass",
    # FunctionDef with varargs as unpacked Tuple *and* TypeVarTuple
    "def f(*args: *tuple[int, *Ts]): pass",
    # FunctionDef with kwargs
    "def f(**kwargs): pass",
    # FunctionDef with all kind of args and docstring
    "def f(a, b=1, c=None, d=[], e={}, *args, f=42, **kwargs): 'doc for f()'",
    # FunctionDef with type annotation on return involving unpacking
    "def f() -> tuple[*Ts]: pass",
    "def f() -> tuple[int, *Ts]: pass",
    "def f() -> tuple[int, *tuple[int, ...]]: pass",
    # ClassDef
    "class C:pass",
    # ClassDef with docstring
    "class C: 'docstring for class C'",
    # ClassDef, new style class
    "class C(object): pass",
    # Classdef with multiple bases
    "class C(A, B): pass",
    # Return
    "def f():return 1",
    "def f():return",
    # Delete
    "del v",
    # Assign
    "v = 1",
    "a,b = c",
    "(a,b) = c",
    "[a,b] = c",
    "a[b] = c",
    # AnnAssign with unpacked types
    "x: tuple[*Ts]",
    "x: tuple[int, *Ts]",
    "x: tuple[int, *tuple[str, ...]]",
    # AugAssign
    "v += 1",
    "v -= 1",
    "v *= 1",
    "v @= 1",
    "v /= 1",
    "v %= 1",
    "v **= 1",
    "v <<= 1",
    "v >>= 1",
    "v |= 1",
    "v ^= 1",
    "v &= 1",
    "v //= 1",
    # For
    "for v in v:pass",
    # For-Else
    "for v in v:\n  pass\nelse:\n  pass",
    # While
    "while v:pass",
    # While-Else
    "while v:\n  pass\nelse:\n  pass",
    # If-Elif-Else
    "if v:pass",
    "if a:\n  pass\nelif b:\n  pass",
    "if a:\n  pass\nelse:\n  pass",
    "if a:\n  pass\nelif b:\n  pass\nelse:\n  pass",
    "if a:\n  pass\nelif b:\n  pass\nelif b:\n  pass\nelif b:\n  pass\nelse:\n  pass",
    # With
    "with x: pass",
    "with x, y: pass",
    "with x as y: pass",
    "with x as y, z as q: pass",
    "with (x as y): pass",
    "with (x, y): pass",
    # Raise
    "raise",
    "raise Exception('string')",
    "raise Exception",
    "raise Exception('string') from None",
    # TryExcept
    "try:\n  pass\nexcept Exception:\n  pass",
    "try:\n  pass\nexcept Exception as exc:\n  pass",
    # TryFinally
    "try:\n  pass\nfinally:\n  pass",
    # TryStarExcept
    "try:\n  pass\nexcept* Exception:\n  pass",
    "try:\n  pass\nexcept* Exception as exc:\n  pass",
    # TryExceptFinallyElse
    "try:\n  pass\nexcept Exception:\n  pass\nelse:  pass\nfinally:\n  pass",
    "try:\n  pass\nexcept Exception as exc:\n  pass\nelse:  pass\nfinally:\n  pass",
    "try:\n  pass\nexcept* Exception as exc:\n  pass\nelse:  pass\nfinally:\n  pass",
    # Assert
    "assert v",
    # Assert with message
    "assert v, 'message'",
    # Import
    "import sys",
    "import foo as bar",
    # ImportFrom
    "from sys import x as y",
    "from sys import v",
    # Global
    "global v",
    # Expr
    "1",
    # Pass,
    "pass",
    # Break
    "for v in v:break",
    # Continue
    "for v in v:continue",
    # for statements with naked tuples (see http://bugs.python.org/issue6704)
    "for a,b in c: pass",
    "for (a,b) in c: pass",
    "for [a,b] in c: pass",
    # Multiline generator expression (test for .lineno & .col_offset)
    """(
    (
    Aa
    ,
       Bb
    )
    for
    Aa
    ,
    Bb in Cc
    )""",
    # dictcomp
    "{a : b for w in x for m in p if g}",
    # dictcomp with naked tuple
    "{a : b for v,w in x}",
    # setcomp
    "{r for l in x if g}",
    # setcomp with naked tuple
    "{r for l,m in x}",
    # AsyncFunctionDef
    "async def f():\n 'async function'\n await something()",
    # AsyncFor
    "async def f():\n async for e in i: 1\n else: 2",
    # AsyncWith
    "async def f():\n async with a as b: 1",
    # PEP 448: Additional Unpacking Generalizations
    "{**{1:2}, 2:3}",
    "{*{1, 2}, 3}",
    # Function with yield (from)
    "def f(): yield 1",
    "def f(): yield from []",
    # Asynchronous comprehensions
    "async def f():\n [i async for b in c]",
    # Decorated FunctionDef
    "@deco1\n@deco2()\n@deco3(1)\ndef f(): pass",
    # Decorated AsyncFunctionDef
    "@deco1\n@deco2()\n@deco3(1)\nasync def f(): pass",
    # Decorated ClassDef
    "@deco1\n@deco2()\n@deco3(1)\nclass C: pass",
    # Decorator with generator argument
    "@deco(a for a in b)\ndef f(): pass",
    # Decorator with attribute
    "@a.b.c\ndef f(): pass",
    # Simple assignment expression
    "(a := 1)",
    # Assignment expression in if statement
    "if a := foo(): pass",
    # Assignment expression in while
    "while a := foo(): pass",
    # Positional-only arguments
    "def f(a, /,): pass",
    "def f(a, /, c, d, e): pass",
    "def f(a, /, c, *, d, e): pass",
    "def f(a, /, c, *, d, e, **kwargs): pass",
    # Positional-only arguments with defaults
    "def f(a=1, /,): pass",
    "def f(a=1, /, b=2, c=4): pass",
    "def f(a=1, /, b=2, *, c=4): pass",
    "def f(a=1, /, b=2, *, c): pass",
    "def f(a=1, /, b=2, *, c=4, **kwargs): pass",
    "def f(a=1, /, b=2, *, c, **kwargs): pass",
    # Type aliases
    "type X = int",
    "type X[T] = int",
    "type X[T, *Ts, **P] = (T, Ts, P)",
    "type X[T: int, *Ts, **P] = (T, Ts, P)",
    "type X[T: (int, str), *Ts, **P] = (T, Ts, P)",
    "type X[T: int = 1, *Ts = 2, **P =3] = (T, Ts, P)",
    # Generic classes
    "class X[T]: pass",
    "class X[T, *Ts, **P]: pass",
    "class X[T: int, *Ts, **P]: pass",
    "class X[T: (int, str), *Ts, **P]: pass",
    "class X[T: int = 1, *Ts = 2, **P = 3]: pass",
    # Generic functions
    "def f[T](): pass",
    "def f[T, *Ts, **P](): pass",
    "def f[T: int, *Ts, **P](): pass",
    "def f[T: (int, str), *Ts, **P](): pass",
    "def f[T: int = 1, *Ts = 2, **P = 3](): pass",
    # Match
    "match x:\n\tcase 1:\n\t\tpass",
    # Match with _
    "match x:\n\tcase 1:\n\t\tpass\n\tcase _:\n\t\tpass",
]

# These are compiled through "single"
# because of overlap with "eval", it just tests what
# can't be tested with "eval"
single_tests = [
    "1+2"
]

# These are compiled through "eval"
# It should test all expressions
eval_tests = [
  # Constant(value=None)
  "None",
  # True
  "True",
  # False
  "False",
  # BoolOp
  "a and b",
  "a or b",
  # BinOp
  "a + b",
  "a - b",
  "a * b",
  "a / b",
  "a @ b",
  "a // b",
  "a ** b",
  "a % b",
  "a >> b",
  "a << b",
  "a ^ b",
  "a | b",
  "a & b",
  # UnaryOp
  "not v",
  "+v",
  "-v",
  "~v",
  # Lambda
  "lambda:None",
  # Dict
  "{ 1:2 }",
  # Empty dict
  "{}",
  # Set
  "{None,}",
  # Multiline dict (test for .lineno & .col_offset)
  """{
      1
        :
          2
     }""",
  # Multiline list
  """[
      1
       ,
        1
     ]""",
  # Multiline tuple
  """(
      1
       ,
     )""",
  # Multiline set
  """{
      1
       ,
        1
     }""",
  # ListComp
  "[a for b in c if d]",
  # GeneratorExp
  "(a for b in c if d)",
  # SetComp
  "{a for b in c if d}",
  # DictComp
  "{k: v for k, v in c if d}",
  # Comprehensions with multiple for targets
  "[(a,b) for a,b in c]",
  "[(a,b) for (a,b) in c]",
  "[(a,b) for [a,b] in c]",
  "{(a,b) for a,b in c}",
  "{(a,b) for (a,b) in c}",
  "{(a,b) for [a,b] in c}",
  "((a,b) for a,b in c)",
  "((a,b) for (a,b) in c)",
  "((a,b) for [a,b] in c)",
  # Async comprehensions - async comprehensions can't work outside an asynchronous function
  #
  # Yield - yield expressions can't work outside a function
  #
  # Compare
  "1 < 2 < 3",
  "a == b",
  "a <= b",
  "a >= b",
  "a != b",
  "a is b",
  "a is not b",
  "a in b",
  "a not in b",
  # Call without argument
  "f()",
  # Call
  "f(1,2,c=3,*d,**e)",
  # Call with multi-character starred
  "f(*[0, 1])",
  # Call with a generator argument
  "f(a for a in b)",
  # Constant(value=int())
  "10",
  # Complex num
  "1j",
  # Constant(value=str())
  "'string'",
  # Attribute
  "a.b",
  # Subscript
  "a[b:c]",
  # Name
  "v",
  # List
  "[1,2,3]",
  # Empty list
  "[]",
  # Tuple
  "1,2,3",
  # Tuple
  "(1,2,3)",
  # Empty tuple
  "()",
  # Combination
  "a.b.c.d(a.b[1:2])",
  # Slice
  "[5][1:]",
  "[5][:1]",
  "[5][::1]",
  "[5][1:1:1]",
  # IfExp
  "foo() if x else bar()",
  # JoinedStr and FormattedValue
  "f'{a}'",
  "f'{a:.2f}'",
  "f'{a!r}'",
  "f'foo({a})'",
]


class AST_Tests(unittest.TestCase):
    maxDiff = None

    def _is_ast_node(self, name, node):
        if not isinstance(node, type):
            return False
        if "ast" not in node.__module__:
            return False
        return name != 'AST' and name[0].isupper()

    def _assertTrueorder(self, ast_node, parent_pos):
        if not isinstance(ast_node, ast.AST) or ast_node._fields is None:
            return
        if isinstance(ast_node, (ast.expr, ast.stmt, ast.excepthandler)):
            node_pos = (ast_node.lineno, ast_node.col_offset)
            self.assertGreaterEqual(node_pos, parent_pos)
            parent_pos = (ast_node.lineno, ast_node.col_offset)
        for name in ast_node._fields:
            value = getattr(ast_node, name)
            if isinstance(value, list):
                first_pos = parent_pos
                if value and name == 'decorator_list':
                    first_pos = (value[0].lineno, value[0].col_offset)
                for child in value:
                    self._assertTrueorder(child, first_pos)
            elif value is not None:
                self._assertTrueorder(value, parent_pos)
        self.assertEqual(ast_node._fields, ast_node.__match_args__)

    def test_AST_objects(self):
        x = ast.AST()
        self.assertEqual(x._fields, ())
        x.foobar = 42
        self.assertEqual(x.foobar, 42)
        self.assertEqual(x.__dict__["foobar"], 42)

        with self.assertRaises(AttributeError):
            x.vararg

        with self.assertRaises(TypeError):
            # "ast.AST constructor takes 0 positional arguments"
            ast.AST(2)

    def test_AST_garbage_collection(self):
        class X:
            pass
        a = ast.AST()
        a.x = X()
        a.x.a = a
        ref = weakref.ref(a.x)
        del a
        support.gc_collect()
        self.assertIsNone(ref())

    def test_snippets(self):
        for input, output, kind in ((exec_tests, exec_results, "exec"),
                                    (single_tests, single_results, "single"),
                                    (eval_tests, eval_results, "eval")):
            for i, o in zip(input, output):
                with self.subTest(action="parsing", input=i):
                    ast_tree = compile(i, "?", kind, ast.PyCF_ONLY_AST)
                    self.assertEqual(to_tuple(ast_tree), o)
                    self._assertTrueorder(ast_tree, (0, 0))
                with self.subTest(action="compiling", input=i, kind=kind):
                    compile(ast_tree, "?", kind)

    def test_ast_validation(self):
        # compile() is the only function that calls PyAST_Validate
        snippets_to_validate = exec_tests + single_tests + eval_tests
        for snippet in snippets_to_validate:
            tree = ast.parse(snippet)
            compile(tree, '<string>', 'exec')

    def test_optimization_levels__debug__(self):
        cases = [(-1, '__debug__'), (0, '__debug__'), (1, False), (2, False)]
        for (optval, expected) in cases:
            with self.subTest(optval=optval, expected=expected):
                res1 = ast.parse("__debug__", optimize=optval)
                res2 = ast.parse(ast.parse("__debug__"), optimize=optval)
                for res in [res1, res2]:
                    self.assertIsInstance(res.body[0], ast.Expr)
                    if isinstance(expected, bool):
                        self.assertIsInstance(res.body[0].value, ast.Constant)
                        self.assertEqual(res.body[0].value.value, expected)
                    else:
                        self.assertIsInstance(res.body[0].value, ast.Name)
                        self.assertEqual(res.body[0].value.id, expected)

    def test_optimization_levels_const_folding(self):
        folded = ('Expr', (1, 0, 1, 5), ('Constant', (1, 0, 1, 5), 3, None))
        not_folded = ('Expr', (1, 0, 1, 5),
                         ('BinOp', (1, 0, 1, 5),
                             ('Constant', (1, 0, 1, 1), 1, None),
                             ('Add',),
                             ('Constant', (1, 4, 1, 5), 2, None)))

        cases = [(-1, not_folded), (0, not_folded), (1, folded), (2, folded)]
        for (optval, expected) in cases:
            with self.subTest(optval=optval):
                tree1 = ast.parse("1 + 2", optimize=optval)
                tree2 = ast.parse(ast.parse("1 + 2"), optimize=optval)
                for tree in [tree1, tree2]:
                    res = to_tuple(tree.body[0])
                    self.assertEqual(res, expected)

    def test_invalid_position_information(self):
        invalid_linenos = [
            (10, 1), (-10, -11), (10, -11), (-5, -2), (-5, 1)
        ]

        for lineno, end_lineno in invalid_linenos:
            with self.subTest(f"Check invalid linenos {lineno}:{end_lineno}"):
                snippet = "a = 1"
                tree = ast.parse(snippet)
                tree.body[0].lineno = lineno
                tree.body[0].end_lineno = end_lineno
                with self.assertRaises(ValueError):
                    compile(tree, '<string>', 'exec')

        invalid_col_offsets = [
            (10, 1), (-10, -11), (10, -11), (-5, -2), (-5, 1)
        ]
        for col_offset, end_col_offset in invalid_col_offsets:
            with self.subTest(f"Check invalid col_offset {col_offset}:{end_col_offset}"):
                snippet = "a = 1"
                tree = ast.parse(snippet)
                tree.body[0].col_offset = col_offset
                tree.body[0].end_col_offset = end_col_offset
                with self.assertRaises(ValueError):
                    compile(tree, '<string>', 'exec')

    def test_compilation_of_ast_nodes_with_default_end_position_values(self):
        tree = ast.Module(body=[
            ast.Import(names=[ast.alias(name='builtins', lineno=1, col_offset=0)], lineno=1, col_offset=0),
            ast.Import(names=[ast.alias(name='traceback', lineno=0, col_offset=0)], lineno=0, col_offset=1)
        ], type_ignores=[])

        # Check that compilation doesn't crash. Note: this may crash explicitly only on debug mode.
        compile(tree, "<string>", "exec")

    def test_slice(self):
        slc = ast.parse("x[::]").body[0].value.slice
        self.assertIsNone(slc.upper)
        self.assertIsNone(slc.lower)
        self.assertIsNone(slc.step)

    def test_from_import(self):
        im = ast.parse("from . import y").body[0]
        self.assertIsNone(im.module)

    def test_non_interned_future_from_ast(self):
        mod = ast.parse("from __future__ import division")
        self.assertIsInstance(mod.body[0], ast.ImportFrom)
        mod.body[0].module = " __future__ ".strip()
        compile(mod, "<test>", "exec")

    def test_alias(self):
        im = ast.parse("from bar import y").body[0]
        self.assertEqual(len(im.names), 1)
        alias = im.names[0]
        self.assertEqual(alias.name, 'y')
        self.assertIsNone(alias.asname)
        self.assertEqual(alias.lineno, 1)
        self.assertEqual(alias.end_lineno, 1)
        self.assertEqual(alias.col_offset, 16)
        self.assertEqual(alias.end_col_offset, 17)

        im = ast.parse("from bar import *").body[0]
        alias = im.names[0]
        self.assertEqual(alias.name, '*')
        self.assertIsNone(alias.asname)
        self.assertEqual(alias.lineno, 1)
        self.assertEqual(alias.end_lineno, 1)
        self.assertEqual(alias.col_offset, 16)
        self.assertEqual(alias.end_col_offset, 17)

        im = ast.parse("from bar import y as z").body[0]
        alias = im.names[0]
        self.assertEqual(alias.name, "y")
        self.assertEqual(alias.asname, "z")
        self.assertEqual(alias.lineno, 1)
        self.assertEqual(alias.end_lineno, 1)
        self.assertEqual(alias.col_offset, 16)
        self.assertEqual(alias.end_col_offset, 22)

        im = ast.parse("import bar as foo").body[0]
        alias = im.names[0]
        self.assertEqual(alias.name, "bar")
        self.assertEqual(alias.asname, "foo")
        self.assertEqual(alias.lineno, 1)
        self.assertEqual(alias.end_lineno, 1)
        self.assertEqual(alias.col_offset, 7)
        self.assertEqual(alias.end_col_offset, 17)

    def test_base_classes(self):
        self.assertTrue(issubclass(ast.For, ast.stmt))
        self.assertTrue(issubclass(ast.Name, ast.expr))
        self.assertTrue(issubclass(ast.stmt, ast.AST))
        self.assertTrue(issubclass(ast.expr, ast.AST))
        self.assertTrue(issubclass(ast.comprehension, ast.AST))
        self.assertTrue(issubclass(ast.Gt, ast.AST))

    def test_field_attr_existence(self):
        for name, item in ast.__dict__.items():
            # constructor has a different signature
            if name == 'Index':
                continue
            if self._is_ast_node(name, item):
                x = self._construct_ast_class(item)
                if isinstance(x, ast.AST):
                    self.assertIs(type(x._fields), tuple)

    def _construct_ast_class(self, cls):
        kwargs = {}
        for name, typ in cls.__annotations__.items():
            if typ is str:
                kwargs[name] = 'capybara'
            elif typ is int:
                kwargs[name] = 42
            elif typ is object:
                kwargs[name] = b'capybara'
            elif isinstance(typ, type) and issubclass(typ, ast.AST):
                kwargs[name] = self._construct_ast_class(typ)
        return cls(**kwargs)

    def test_arguments(self):
        x = ast.arguments()
        self.assertEqual(x._fields, ('posonlyargs', 'args', 'vararg', 'kwonlyargs',
                                     'kw_defaults', 'kwarg', 'defaults'))
        self.assertEqual(x.__annotations__, {
            'posonlyargs': list[ast.arg],
            'args': list[ast.arg],
            'vararg': ast.arg | None,
            'kwonlyargs': list[ast.arg],
            'kw_defaults': list[ast.expr],
            'kwarg': ast.arg | None,
            'defaults': list[ast.expr],
        })

        self.assertEqual(x.args, [])
        self.assertIsNone(x.vararg)

        x = ast.arguments(*range(1, 8))
        self.assertEqual(x.args, 2)
        self.assertEqual(x.vararg, 3)

    def test_field_attr_writable(self):
        x = ast.Constant(1)
        # We can assign to _fields
        x._fields = 666
        self.assertEqual(x._fields, 666)

    def test_classattrs(self):
        with self.assertWarns(DeprecationWarning):
            x = ast.Constant()
        self.assertEqual(x._fields, ('value', 'kind'))

        with self.assertRaises(AttributeError):
            x.value

        x = ast.Constant(42)
        self.assertEqual(x.value, 42)

        with self.assertRaises(AttributeError):
            x.lineno

        with self.assertRaises(AttributeError):
            x.foobar

        x = ast.Constant(lineno=2, value=3)
        self.assertEqual(x.lineno, 2)

        x = ast.Constant(42, lineno=0)
        self.assertEqual(x.lineno, 0)
        self.assertEqual(x._fields, ('value', 'kind'))
        self.assertEqual(x.value, 42)

        self.assertRaises(TypeError, ast.Constant, 1, None, 2)
        self.assertRaises(TypeError, ast.Constant, 1, None, 2, lineno=0)

        # Arbitrary keyword arguments are supported (but deprecated)
        with self.assertWarns(DeprecationWarning):
            self.assertEqual(ast.Constant(1, foo='bar').foo, 'bar')

        with self.assertRaisesRegex(TypeError, "Constant got multiple values for argument 'value'"):
            ast.Constant(1, value=2)

        self.assertEqual(ast.Constant(42).value, 42)
        self.assertEqual(ast.Constant(4.25).value, 4.25)
        self.assertEqual(ast.Constant(4.25j).value, 4.25j)
        self.assertEqual(ast.Constant('42').value, '42')
        self.assertEqual(ast.Constant(b'42').value, b'42')
        self.assertIs(ast.Constant(True).value, True)
        self.assertIs(ast.Constant(False).value, False)
        self.assertIs(ast.Constant(None).value, None)
        self.assertIs(ast.Constant(...).value, ...)

    def test_constant_subclasses(self):
        class N(ast.Constant):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.z = 'spam'
        class N2(ast.Constant):
            pass

        n = N(42)
        self.assertEqual(n.value, 42)
        self.assertEqual(n.z, 'spam')
        self.assertEqual(type(n), N)
        self.assertTrue(isinstance(n, N))
        self.assertTrue(isinstance(n, ast.Constant))
        self.assertFalse(isinstance(n, N2))
        self.assertFalse(isinstance(ast.Constant(42), N))
        n = N(value=42)
        self.assertEqual(n.value, 42)
        self.assertEqual(type(n), N)

    def test_module(self):
        body = [ast.Constant(42)]
        x = ast.Module(body, [])
        self.assertEqual(x.body, body)

    def test_nodeclasses(self):
        # Zero arguments constructor explicitly allowed (but deprecated)
        with self.assertWarns(DeprecationWarning):
            x = ast.BinOp()
        self.assertEqual(x._fields, ('left', 'op', 'right'))

        # Random attribute allowed too
        x.foobarbaz = 5
        self.assertEqual(x.foobarbaz, 5)

        n1 = ast.Constant(1)
        n3 = ast.Constant(3)
        addop = ast.Add()
        x = ast.BinOp(n1, addop, n3)
        self.assertEqual(x.left, n1)
        self.assertEqual(x.op, addop)
        self.assertEqual(x.right, n3)

        x = ast.BinOp(1, 2, 3)
        self.assertEqual(x.left, 1)
        self.assertEqual(x.op, 2)
        self.assertEqual(x.right, 3)

        x = ast.BinOp(1, 2, 3, lineno=0)
        self.assertEqual(x.left, 1)
        self.assertEqual(x.op, 2)
        self.assertEqual(x.right, 3)
        self.assertEqual(x.lineno, 0)

        # node raises exception when given too many arguments
        self.assertRaises(TypeError, ast.BinOp, 1, 2, 3, 4)
        # node raises exception when given too many arguments
        self.assertRaises(TypeError, ast.BinOp, 1, 2, 3, 4, lineno=0)

        # can set attributes through kwargs too
        x = ast.BinOp(left=1, op=2, right=3, lineno=0)
        self.assertEqual(x.left, 1)
        self.assertEqual(x.op, 2)
        self.assertEqual(x.right, 3)
        self.assertEqual(x.lineno, 0)

        # Random kwargs also allowed (but deprecated)
        with self.assertWarns(DeprecationWarning):
            x = ast.BinOp(1, 2, 3, foobarbaz=42)
        self.assertEqual(x.foobarbaz, 42)

    def test_no_fields(self):
        # this used to fail because Sub._fields was None
        x = ast.Sub()
        self.assertEqual(x._fields, ())

    def test_invalid_sum(self):
        pos = dict(lineno=2, col_offset=3)
        m = ast.Module([ast.Expr(ast.expr(**pos), **pos)], [])
        with self.assertRaises(TypeError) as cm:
            compile(m, "<test>", "exec")
        self.assertIn("but got <ast.expr", str(cm.exception))

    def test_invalid_identifier(self):
        m = ast.Module([ast.Expr(ast.Name(42, ast.Load()))], [])
        ast.fix_missing_locations(m)
        with self.assertRaises(TypeError) as cm:
            compile(m, "<test>", "exec")
        self.assertIn("identifier must be of type str", str(cm.exception))

    def test_invalid_constant(self):
        for invalid_constant in int, (1, 2, int), frozenset((1, 2, int)):
            e = ast.Expression(body=ast.Constant(invalid_constant))
            ast.fix_missing_locations(e)
            with self.assertRaisesRegex(
                TypeError, "invalid type in Constant: type"
            ):
                compile(e, "<test>", "eval")

    def test_empty_yield_from(self):
        # Issue 16546: yield from value is not optional.
        empty_yield_from = ast.parse("def f():\n yield from g()")
        empty_yield_from.body[0].body[0].value.value = None
        with self.assertRaises(ValueError) as cm:
            compile(empty_yield_from, "<test>", "exec")
        self.assertIn("field 'value' is required", str(cm.exception))

    @support.cpython_only
    def test_issue31592(self):
        # There shouldn't be an assertion failure in case of a bad
        # unicodedata.normalize().
        import unicodedata
        def bad_normalize(*args):
            return None
        with support.swap_attr(unicodedata, 'normalize', bad_normalize):
            self.assertRaises(TypeError, ast.parse, '\u03D5')

    def test_issue18374_binop_col_offset(self):
        tree = ast.parse('4+5+6+7')
        parent_binop = tree.body[0].value
        child_binop = parent_binop.left
        grandchild_binop = child_binop.left
        self.assertEqual(parent_binop.col_offset, 0)
        self.assertEqual(parent_binop.end_col_offset, 7)
        self.assertEqual(child_binop.col_offset, 0)
        self.assertEqual(child_binop.end_col_offset, 5)
        self.assertEqual(grandchild_binop.col_offset, 0)
        self.assertEqual(grandchild_binop.end_col_offset, 3)

        tree = ast.parse('4+5-\\\n 6-7')
        parent_binop = tree.body[0].value
        child_binop = parent_binop.left
        grandchild_binop = child_binop.left
        self.assertEqual(parent_binop.col_offset, 0)
        self.assertEqual(parent_binop.lineno, 1)
        self.assertEqual(parent_binop.end_col_offset, 4)
        self.assertEqual(parent_binop.end_lineno, 2)

        self.assertEqual(child_binop.col_offset, 0)
        self.assertEqual(child_binop.lineno, 1)
        self.assertEqual(child_binop.end_col_offset, 2)
        self.assertEqual(child_binop.end_lineno, 2)

        self.assertEqual(grandchild_binop.col_offset, 0)
        self.assertEqual(grandchild_binop.lineno, 1)
        self.assertEqual(grandchild_binop.end_col_offset, 3)
        self.assertEqual(grandchild_binop.end_lineno, 1)

    def test_issue39579_dotted_name_end_col_offset(self):
        tree = ast.parse('@a.b.c\ndef f(): pass')
        attr_b = tree.body[0].decorator_list[0].value
        self.assertEqual(attr_b.end_col_offset, 4)

    def test_ast_asdl_signature(self):
        self.assertEqual(ast.withitem.__doc__, "withitem(expr context_expr, expr? optional_vars)")
        self.assertEqual(ast.GtE.__doc__, "GtE")
        self.assertEqual(ast.Name.__doc__, "Name(identifier id, expr_context ctx)")
        self.assertEqual(ast.cmpop.__doc__, "cmpop = Eq | NotEq | Lt | LtE | Gt | GtE | Is | IsNot | In | NotIn")
        expressions = [f"     | {node.__doc__}" for node in ast.expr.__subclasses__()]
        expressions[0] = f"expr = {ast.expr.__subclasses__()[0].__doc__}"
        self.assertCountEqual(ast.expr.__doc__.split("\n"), expressions)

    def test_compare_basics(self):
        self.assertTrue(ast.compare(ast.parse("x = 10"), ast.parse("x = 10")))
        self.assertFalse(ast.compare(ast.parse("x = 10"), ast.parse("")))
        self.assertFalse(ast.compare(ast.parse("x = 10"), ast.parse("x")))
        self.assertFalse(
            ast.compare(ast.parse("x = 10;y = 20"), ast.parse("class C:pass"))
        )

    def test_compare_modified_ast(self):
        # The ast API is a bit underspecified. The objects are mutable,
        # and even _fields and _attributes are mutable. The compare() does
        # some simple things to accommodate mutability.
        a = ast.parse("m * x + b", mode="eval")
        b = ast.parse("m * x + b", mode="eval")
        self.assertTrue(ast.compare(a, b))

        a._fields = a._fields + ("spam",)
        a.spam = "Spam"
        self.assertNotEqual(a._fields, b._fields)
        self.assertFalse(ast.compare(a, b))
        self.assertFalse(ast.compare(b, a))

        b._fields = a._fields
        b.spam = a.spam
        self.assertTrue(ast.compare(a, b))
        self.assertTrue(ast.compare(b, a))

        b._attributes = b._attributes + ("eggs",)
        b.eggs = "eggs"
        self.assertNotEqual(a._attributes, b._attributes)
        self.assertFalse(ast.compare(a, b, compare_attributes=True))
        self.assertFalse(ast.compare(b, a, compare_attributes=True))

        a._attributes = b._attributes
        a.eggs = b.eggs
        self.assertTrue(ast.compare(a, b, compare_attributes=True))
        self.assertTrue(ast.compare(b, a, compare_attributes=True))

    def test_compare_literals(self):
        constants = (
            -20,
            20,
            20.0,
            1,
            1.0,
            True,
            0,
            False,
            frozenset(),
            tuple(),
            "ABCD",
            "abcd",
            "中文字",
            1e1000,
            -1e1000,
        )
        for next_index, constant in enumerate(constants[:-1], 1):
            next_constant = constants[next_index]
            with self.subTest(literal=constant, next_literal=next_constant):
                self.assertTrue(
                    ast.compare(ast.Constant(constant), ast.Constant(constant))
                )
                self.assertFalse(
                    ast.compare(
                        ast.Constant(constant), ast.Constant(next_constant)
                    )
                )

        same_looking_literal_cases = [
            {1, 1.0, True, 1 + 0j},
            {0, 0.0, False, 0 + 0j},
        ]
        for same_looking_literals in same_looking_literal_cases:
            for literal in same_looking_literals:
                for same_looking_literal in same_looking_literals - {literal}:
                    self.assertFalse(
                        ast.compare(
                            ast.Constant(literal),
                            ast.Constant(same_looking_literal),
                        )
                    )

    def test_compare_fieldless(self):
        self.assertTrue(ast.compare(ast.Add(), ast.Add()))
        self.assertFalse(ast.compare(ast.Sub(), ast.Add()))

        # test that missing runtime fields is handled in ast.compare()
        a1, a2 = ast.Name('a'), ast.Name('a')
        self.assertTrue(ast.compare(a1, a2))
        self.assertTrue(ast.compare(a1, a2))
        del a1.id
        self.assertFalse(ast.compare(a1, a2))
        del a2.id
        self.assertTrue(ast.compare(a1, a2))

    def test_compare_modes(self):
        for mode, sources in (
            ("exec", exec_tests),
            ("eval", eval_tests),
            ("single", single_tests),
        ):
            for source in sources:
                a = ast.parse(source, mode=mode)
                b = ast.parse(source, mode=mode)
                self.assertTrue(
                    ast.compare(a, b), f"{ast.dump(a)} != {ast.dump(b)}"
                )

    def test_compare_attributes_option(self):
        def parse(a, b):
            return ast.parse(a), ast.parse(b)

        a, b = parse("2 + 2", "2+2")
        self.assertTrue(ast.compare(a, b))
        self.assertTrue(ast.compare(a, b, compare_attributes=False))
        self.assertFalse(ast.compare(a, b, compare_attributes=True))

    def test_compare_attributes_option_missing_attribute(self):
        # test that missing runtime attributes is handled in ast.compare()
        a1, a2 = ast.Name('a', lineno=1), ast.Name('a', lineno=1)
        self.assertTrue(ast.compare(a1, a2))
        self.assertTrue(ast.compare(a1, a2, compare_attributes=True))
        del a1.lineno
        self.assertFalse(ast.compare(a1, a2, compare_attributes=True))
        del a2.lineno
        self.assertTrue(ast.compare(a1, a2, compare_attributes=True))

    def test_positional_only_feature_version(self):
        ast.parse('def foo(x, /): ...', feature_version=(3, 8))
        ast.parse('def bar(x=1, /): ...', feature_version=(3, 8))
        with self.assertRaises(SyntaxError):
            ast.parse('def foo(x, /): ...', feature_version=(3, 7))
        with self.assertRaises(SyntaxError):
            ast.parse('def bar(x=1, /): ...', feature_version=(3, 7))

        ast.parse('lambda x, /: ...', feature_version=(3, 8))
        ast.parse('lambda x=1, /: ...', feature_version=(3, 8))
        with self.assertRaises(SyntaxError):
            ast.parse('lambda x, /: ...', feature_version=(3, 7))
        with self.assertRaises(SyntaxError):
            ast.parse('lambda x=1, /: ...', feature_version=(3, 7))

    def test_assignment_expression_feature_version(self):
        ast.parse('(x := 0)', feature_version=(3, 8))
        with self.assertRaises(SyntaxError):
            ast.parse('(x := 0)', feature_version=(3, 7))

    def test_conditional_context_managers_parse_with_low_feature_version(self):
        # regression test for gh-115881
        ast.parse('with (x() if y else z()): ...', feature_version=(3, 8))

    def test_exception_groups_feature_version(self):
        code = dedent('''
        try: ...
        except* Exception: ...
        ''')
        ast.parse(code)
        with self.assertRaises(SyntaxError):
            ast.parse(code, feature_version=(3, 10))

    def test_type_params_feature_version(self):
        samples = [
            "type X = int",
            "class X[T]: pass",
            "def f[T](): pass",
        ]
        for sample in samples:
            with self.subTest(sample):
                ast.parse(sample)
                with self.assertRaises(SyntaxError):
                    ast.parse(sample, feature_version=(3, 11))

    def test_type_params_default_feature_version(self):
        samples = [
            "type X[*Ts=int] = int",
            "class X[T=int]: pass",
            "def f[**P=int](): pass",
        ]
        for sample in samples:
            with self.subTest(sample):
                ast.parse(sample)
                with self.assertRaises(SyntaxError):
                    ast.parse(sample, feature_version=(3, 12))

    def test_invalid_major_feature_version(self):
        with self.assertRaises(ValueError):
            ast.parse('pass', feature_version=(2, 7))
        with self.assertRaises(ValueError):
            ast.parse('pass', feature_version=(4, 0))

    def test_constant_as_name(self):
        for constant in "True", "False", "None":
            expr = ast.Expression(ast.Name(constant, ast.Load()))
            ast.fix_missing_locations(expr)
            with self.assertRaisesRegex(ValueError, f"identifier field can't represent '{constant}' constant"):
                compile(expr, "<test>", "eval")

    def test_precedence_enum(self):
        class _Precedence(enum.IntEnum):
            """Precedence table that originated from python grammar."""
            NAMED_EXPR = enum.auto()      # <target> := <expr1>
            TUPLE = enum.auto()           # <expr1>, <expr2>
            YIELD = enum.auto()           # 'yield', 'yield from'
            TEST = enum.auto()            # 'if'-'else', 'lambda'
            OR = enum.auto()              # 'or'
            AND = enum.auto()             # 'and'
            NOT = enum.auto()             # 'not'
            CMP = enum.auto()             # '<', '>', '==', '>=', '<=', '!=',
                                          # 'in', 'not in', 'is', 'is not'
            EXPR = enum.auto()
            BOR = EXPR                    # '|'
            BXOR = enum.auto()            # '^'
            BAND = enum.auto()            # '&'
            SHIFT = enum.auto()           # '<<', '>>'
            ARITH = enum.auto()           # '+', '-'
            TERM = enum.auto()            # '*', '@', '/', '%', '//'
            FACTOR = enum.auto()          # unary '+', '-', '~'
            POWER = enum.auto()           # '**'
            AWAIT = enum.auto()           # 'await'
            ATOM = enum.auto()
            def next(self):
                try:
                    return self.__class__(self + 1)
                except ValueError:
                    return self
        enum._test_simple_enum(_Precedence, ast._Precedence)

    @support.cpython_only
    def test_ast_recursion_limit(self):
        fail_depth = support.exceeds_recursion_limit()
        crash_depth = 100_000
        success_depth = int(support.get_c_recursion_limit() * 0.8)
        if _testinternalcapi is not None:
            remaining = _testinternalcapi.get_c_recursion_remaining()
            success_depth = min(success_depth, remaining)

        def check_limit(prefix, repeated):
            expect_ok = prefix + repeated * success_depth
            ast.parse(expect_ok)
            for depth in (fail_depth, crash_depth):
                broken = prefix + repeated * depth
                details = "Compiling ({!r} + {!r} * {})".format(
                            prefix, repeated, depth)
                with self.assertRaises(RecursionError, msg=details):
                    with support.infinite_recursion():
                        ast.parse(broken)

        check_limit("a", "()")
        check_limit("a", ".b")
        check_limit("a", "[0]")
        check_limit("a", "*a")

    def test_null_bytes(self):
        with self.assertRaises(SyntaxError,
            msg="source code string cannot contain null bytes"):
            ast.parse("a\0b")

    def assert_none_check(self, node: type[ast.AST], attr: str, source: str) -> None:
        with self.subTest(f"{node.__name__}.{attr}"):
            tree = ast.parse(source)
            found = 0
            for child in ast.walk(tree):
                if isinstance(child, node):
                    setattr(child, attr, None)
                    found += 1
            self.assertEqual(found, 1)
            e = re.escape(f"field '{attr}' is required for {node.__name__}")
            with self.assertRaisesRegex(ValueError, f"^{e}$"):
                compile(tree, "<test>", "exec")

    def test_none_checks(self) -> None:
        tests = [
            (ast.alias, "name", "import spam as SPAM"),
            (ast.arg, "arg", "def spam(SPAM): spam"),
            (ast.comprehension, "target", "[spam for SPAM in spam]"),
            (ast.comprehension, "iter", "[spam for spam in SPAM]"),
            (ast.keyword, "value", "spam(**SPAM)"),
            (ast.match_case, "pattern", "match spam:\n case SPAM: spam"),
            (ast.withitem, "context_expr", "with SPAM: spam"),
        ]
        for node, attr, source in tests:
            self.assert_none_check(node, attr, source)


class CopyTests(unittest.TestCase):
    """Test copying and pickling AST nodes."""

    @staticmethod
    def iter_ast_classes():
        """Iterate over the (native) subclasses of ast.AST recursively.

        This excludes the special class ast.Index since its constructor
        returns an integer.
        """
        def do(cls):
            if cls.__module__ != 'ast':
                return
            if cls is ast.Index:
                return

            yield cls
            for sub in cls.__subclasses__():
                yield from do(sub)

        yield from do(ast.AST)

    def test_pickling(self):
        import pickle

        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            for code in exec_tests:
                with self.subTest(code=code, protocol=protocol):
                    tree = compile(code, "?", "exec", 0x400)
                    ast2 = pickle.loads(pickle.dumps(tree, protocol))
                    self.assertEqual(to_tuple(ast2), to_tuple(tree))

    def test_copy_with_parents(self):
        # gh-120108
        code = """
        ('',)
        while i < n:
            if ch == '':
                ch = format[i]
                if ch == '':
                    if freplace is None:
                        '' % getattr(object)
                elif ch == '':
                    if zreplace is None:
                        if hasattr:
                            offset = object.utcoffset()
                            if offset is not None:
                                if offset.days < 0:
                                    offset = -offset
                                h = divmod(timedelta(hours=0))
                                if u:
                                    zreplace = '' % (sign,)
                                elif s:
                                    zreplace = '' % (sign,)
                                else:
                                    zreplace = '' % (sign,)
                elif ch == '':
                    if Zreplace is None:
                        Zreplace = ''
                        if hasattr(object):
                            s = object.tzname()
                            if s is not None:
                                Zreplace = s.replace('')
                    newformat.append(Zreplace)
                else:
                    push('')
            else:
                push(ch)

        """
        tree = ast.parse(textwrap.dedent(code))
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
        try:
            with support.infinite_recursion(200):
                tree2 = copy.deepcopy(tree)
        finally:
            # Singletons like ast.Load() are shared; make sure we don't
            # leave them mutated after this test.
            for node in ast.walk(tree):
                if hasattr(node, "parent"):
                    del node.parent

        for node in ast.walk(tree2):
            for child in ast.iter_child_nodes(node):
                if hasattr(child, "parent") and not isinstance(child, (
                    ast.expr_context, ast.boolop, ast.unaryop, ast.cmpop, ast.operator,
                )):
                    self.assertEqual(to_tuple(child.parent), to_tuple(node))

    def test_replace_interface(self):
        for klass in self.iter_ast_classes():
            with self.subTest(klass=klass):
                self.assertTrue(hasattr(klass, '__replace__'))

            fields = set(klass._fields)
            with self.subTest(klass=klass, fields=fields):
                node = klass(**dict.fromkeys(fields))
                # forbid positional arguments in replace()
                self.assertRaises(TypeError, copy.replace, node, 1)
                self.assertRaises(TypeError, node.__replace__, 1)

    def test_replace_native(self):
        for klass in self.iter_ast_classes():
            fields = set(klass._fields)
            attributes = set(klass._attributes)

            with self.subTest(klass=klass, fields=fields, attributes=attributes):
                # use of object() to ensure that '==' and 'is'
                # behave similarly in ast.compare(node, repl)
                old_fields = {field: object() for field in fields}
                old_attrs = {attr: object() for attr in attributes}

                # check shallow copy
                node = klass(**old_fields)
                repl = copy.replace(node)
                self.assertTrue(ast.compare(node, repl, compare_attributes=True))
                # check when passing using attributes (they may be optional!)
                node = klass(**old_fields, **old_attrs)
                repl = copy.replace(node)
                self.assertTrue(ast.compare(node, repl, compare_attributes=True))

                for field in fields:
                    # check when we sometimes have attributes and sometimes not
                    for init_attrs in [{}, old_attrs]:
                        node = klass(**old_fields, **init_attrs)
                        # only change a single field (do not change attributes)
                        new_value = object()
                        repl = copy.replace(node, **{field: new_value})
                        for f in fields:
                            old_value = old_fields[f]
                            # assert that there is no side-effect
                            self.assertIs(getattr(node, f), old_value)
                            # check the changes
                            if f != field:
                                self.assertIs(getattr(repl, f), old_value)
                            else:
                                self.assertIs(getattr(repl, f), new_value)
                        self.assertFalse(ast.compare(node, repl, compare_attributes=True))

                for attribute in attributes:
                    node = klass(**old_fields, **old_attrs)
                    # only change a single attribute (do not change fields)
                    new_attr = object()
                    repl = copy.replace(node, **{attribute: new_attr})
                    for a in attributes:
                        old_attr = old_attrs[a]
                        # assert that there is no side-effect
                        self.assertIs(getattr(node, a), old_attr)
                        # check the changes
                        if a != attribute:
                            self.assertIs(getattr(repl, a), old_attr)
                        else:
                            self.assertIs(getattr(repl, a), new_attr)
                    self.assertFalse(ast.compare(node, repl, compare_attributes=True))

    def test_replace_accept_known_class_fields(self):
        nid, ctx = object(), object()

        node = ast.Name(id=nid, ctx=ctx)
        self.assertIs(node.id, nid)
        self.assertIs(node.ctx, ctx)

        new_nid = object()
        repl = copy.replace(node, id=new_nid)
        # assert that there is no side-effect
        self.assertIs(node.id, nid)
        self.assertIs(node.ctx, ctx)
        # check the changes
        self.assertIs(repl.id, new_nid)
        self.assertIs(repl.ctx, node.ctx)  # no changes

    def test_replace_accept_known_class_attributes(self):
        node = ast.parse('x').body[0].value
        self.assertEqual(node.id, 'x')
        self.assertEqual(node.lineno, 1)

        # constructor allows any type so replace() should do the same
        lineno = object()
        repl = copy.replace(node, lineno=lineno)
        # assert that there is no side-effect
        self.assertEqual(node.lineno, 1)
        # check the changes
        self.assertEqual(repl.id, node.id)
        self.assertEqual(repl.ctx, node.ctx)
        self.assertEqual(repl.lineno, lineno)

        _, _, state = node.__reduce__()
        self.assertEqual(state['id'], 'x')
        self.assertEqual(state['ctx'], node.ctx)
        self.assertEqual(state['lineno'], 1)

        _, _, state = repl.__reduce__()
        self.assertEqual(state['id'], 'x')
        self.assertEqual(state['ctx'], node.ctx)
        self.assertEqual(state['lineno'], lineno)

    def test_replace_accept_known_custom_class_fields(self):
        class MyNode(ast.AST):
            _fields = ('name', 'data')
            __annotations__ = {'name': str, 'data': object}
            __match_args__ = ('name', 'data')

        name, data = 'name', object()

        node = MyNode(name, data)
        self.assertIs(node.name, name)
        self.assertIs(node.data, data)
        # check shallow copy
        repl = copy.replace(node)
        # assert that there is no side-effect
        self.assertIs(node.name, name)
        self.assertIs(node.data, data)
        # check the shallow copy
        self.assertIs(repl.name, name)
        self.assertIs(repl.data, data)

        node = MyNode(name, data)
        repl_data = object()
        # replace custom but known field
        repl = copy.replace(node, data=repl_data)
        # assert that there is no side-effect
        self.assertIs(node.name, name)
        self.assertIs(node.data, data)
        # check the changes
        self.assertIs(repl.name, node.name)
        self.assertIs(repl.data, repl_data)

    def test_replace_accept_known_custom_class_attributes(self):
        class MyNode(ast.AST):
            x = 0
            y = 1
            _attributes = ('x', 'y')

        node = MyNode()
        self.assertEqual(node.x, 0)
        self.assertEqual(node.y, 1)

        y = object()
        # custom attributes are currently not supported and raise a warning
        # because the allowed attributes are hard-coded !
        msg = (
            "MyNode.__init__ got an unexpected keyword argument 'y'. "
            "Support for arbitrary keyword arguments is deprecated and "
            "will be removed in Python 3.15"
        )
        with self.assertWarnsRegex(DeprecationWarning, re.escape(msg)):
            repl = copy.replace(node, y=y)
        # assert that there is no side-effect
        self.assertEqual(node.x, 0)
        self.assertEqual(node.y, 1)
        # check the changes
        self.assertEqual(repl.x, 0)
        self.assertEqual(repl.y, y)

    def test_replace_ignore_known_custom_instance_fields(self):
        node = ast.parse('x').body[0].value
        node.extra = extra = object()  # add instance 'extra' field
        context = node.ctx

        # assert initial values
        self.assertIs(node.id, 'x')
        self.assertIs(node.ctx, context)
        self.assertIs(node.extra, extra)
        # shallow copy, but drops extra fields
        repl = copy.replace(node)
        # assert that there is no side-effect
        self.assertIs(node.id, 'x')
        self.assertIs(node.ctx, context)
        self.assertIs(node.extra, extra)
        # verify that the 'extra' field is not kept
        self.assertIs(repl.id, 'x')
        self.assertIs(repl.ctx, context)
        self.assertRaises(AttributeError, getattr, repl, 'extra')

        # change known native field
        repl = copy.replace(node, id='y')
        # assert that there is no side-effect
        self.assertIs(node.id, 'x')
        self.assertIs(node.ctx, context)
        self.assertIs(node.extra, extra)
        # verify that the 'extra' field is not kept
        self.assertIs(repl.id, 'y')
        self.assertIs(repl.ctx, context)
        self.assertRaises(AttributeError, getattr, repl, 'extra')

    def test_replace_reject_missing_field(self):
        # case: warn if deleted field is not replaced
        node = ast.parse('x').body[0].value
        context = node.ctx
        del node.id

        self.assertRaises(AttributeError, getattr, node, 'id')
        self.assertIs(node.ctx, context)
        msg = "Name.__replace__ missing 1 keyword argument: 'id'."
        with self.assertRaisesRegex(TypeError, re.escape(msg)):
            copy.replace(node)
        # assert that there is no side-effect
        self.assertRaises(AttributeError, getattr, node, 'id')
        self.assertIs(node.ctx, context)

        # case: do not raise if deleted field is replaced
        node = ast.parse('x').body[0].value
        context = node.ctx
        del node.id

        self.assertRaises(AttributeError, getattr, node, 'id')
        self.assertIs(node.ctx, context)
        repl = copy.replace(node, id='y')
        # assert that there is no side-effect
        self.assertRaises(AttributeError, getattr, node, 'id')
        self.assertIs(node.ctx, context)
        self.assertIs(repl.id, 'y')
        self.assertIs(repl.ctx, context)

    def test_replace_reject_known_custom_instance_fields_commits(self):
        node = ast.parse('x').body[0].value
        node.extra = extra = object()  # add instance 'extra' field
        context = node.ctx

        # explicit rejection of known instance fields
        self.assertTrue(hasattr(node, 'extra'))
        msg = "Name.__replace__ got an unexpected keyword argument 'extra'."
        with self.assertRaisesRegex(TypeError, re.escape(msg)):
            copy.replace(node, extra=1)
        # assert that there is no side-effect
        self.assertIs(node.id, 'x')
        self.assertIs(node.ctx, context)
        self.assertIs(node.extra, extra)

    def test_replace_reject_unknown_instance_fields(self):
        node = ast.parse('x').body[0].value
        context = node.ctx

        # explicit rejection of unknown extra fields
        self.assertRaises(AttributeError, getattr, node, 'unknown')
        msg = "Name.__replace__ got an unexpected keyword argument 'unknown'."
        with self.assertRaisesRegex(TypeError, re.escape(msg)):
            copy.replace(node, unknown=1)
        # assert that there is no side-effect
        self.assertIs(node.id, 'x')
        self.assertIs(node.ctx, context)
        self.assertRaises(AttributeError, getattr, node, 'unknown')

class ASTHelpers_Test(unittest.TestCase):
    maxDiff = None

    def test_parse(self):
        a = ast.parse('foo(1 + 1)')
        b = compile('foo(1 + 1)', '<unknown>', 'exec', ast.PyCF_ONLY_AST)
        self.assertEqual(ast.dump(a), ast.dump(b))

    def test_parse_in_error(self):
        try:
            1/0
        except Exception:
            with self.assertRaises(SyntaxError) as e:
                ast.literal_eval(r"'\U'")
            self.assertIsNotNone(e.exception.__context__)

    def test_dump(self):
        node = ast.parse('spam(eggs, "and cheese")')
        self.assertEqual(ast.dump(node),
            "Module(body=[Expr(value=Call(func=Name(id='spam', ctx=Load()), "
            "args=[Name(id='eggs', ctx=Load()), Constant(value='and cheese')]))])"
        )
        self.assertEqual(ast.dump(node, annotate_fields=False),
            "Module([Expr(Call(Name('spam', Load()), [Name('eggs', Load()), "
            "Constant('and cheese')]))])"
        )
        self.assertEqual(ast.dump(node, include_attributes=True),
            "Module(body=[Expr(value=Call(func=Name(id='spam', ctx=Load(), "
            "lineno=1, col_offset=0, end_lineno=1, end_col_offset=4), "
            "args=[Name(id='eggs', ctx=Load(), lineno=1, col_offset=5, "
            "end_lineno=1, end_col_offset=9), Constant(value='and cheese', "
            "lineno=1, col_offset=11, end_lineno=1, end_col_offset=23)], "
            "lineno=1, col_offset=0, end_lineno=1, end_col_offset=24), "
            "lineno=1, col_offset=0, end_lineno=1, end_col_offset=24)])"
        )

    def test_dump_indent(self):
        node = ast.parse('spam(eggs, "and cheese")')
        self.assertEqual(ast.dump(node, indent=3), """\
Module(
   body=[
      Expr(
         value=Call(
            func=Name(id='spam', ctx=Load()),
            args=[
               Name(id='eggs', ctx=Load()),
               Constant(value='and cheese')]))])""")
        self.assertEqual(ast.dump(node, annotate_fields=False, indent='\t'), """\
Module(
\t[
\t\tExpr(
\t\t\tCall(
\t\t\t\tName('spam', Load()),
\t\t\t\t[
\t\t\t\t\tName('eggs', Load()),
\t\t\t\t\tConstant('and cheese')]))])""")
        self.assertEqual(ast.dump(node, include_attributes=True, indent=3), """\
Module(
   body=[
      Expr(
         value=Call(
            func=Name(
               id='spam',
               ctx=Load(),
               lineno=1,
               col_offset=0,
               end_lineno=1,
               end_col_offset=4),
            args=[
               Name(
                  id='eggs',
                  ctx=Load(),
                  lineno=1,
                  col_offset=5,
                  end_lineno=1,
                  end_col_offset=9),
               Constant(
                  value='and cheese',
                  lineno=1,
                  col_offset=11,
                  end_lineno=1,
                  end_col_offset=23)],
            lineno=1,
            col_offset=0,
            end_lineno=1,
            end_col_offset=24),
         lineno=1,
         col_offset=0,
         end_lineno=1,
         end_col_offset=24)])""")

    def test_dump_incomplete(self):
        node = ast.Raise(lineno=3, col_offset=4)
        self.assertEqual(ast.dump(node),
            "Raise()"
        )
        self.assertEqual(ast.dump(node, include_attributes=True),
            "Raise(lineno=3, col_offset=4)"
        )
        node = ast.Raise(exc=ast.Name(id='e', ctx=ast.Load()), lineno=3, col_offset=4)
        self.assertEqual(ast.dump(node),
            "Raise(exc=Name(id='e', ctx=Load()))"
        )
        self.assertEqual(ast.dump(node, annotate_fields=False),
            "Raise(Name('e', Load()))"
        )
        self.assertEqual(ast.dump(node, include_attributes=True),
            "Raise(exc=Name(id='e', ctx=Load()), lineno=3, col_offset=4)"
        )
        self.assertEqual(ast.dump(node, annotate_fields=False, include_attributes=True),
            "Raise(Name('e', Load()), lineno=3, col_offset=4)"
        )
        node = ast.Raise(cause=ast.Name(id='e', ctx=ast.Load()))
        self.assertEqual(ast.dump(node),
            "Raise(cause=Name(id='e', ctx=Load()))"
        )
        self.assertEqual(ast.dump(node, annotate_fields=False),
            "Raise(cause=Name('e', Load()))"
        )
        # Arguments:
        node = ast.arguments(args=[ast.arg("x")])
        self.assertEqual(ast.dump(node, annotate_fields=False),
            "arguments([], [arg('x')])",
        )
        node = ast.arguments(posonlyargs=[ast.arg("x")])
        self.assertEqual(ast.dump(node, annotate_fields=False),
            "arguments([arg('x')])",
        )
        node = ast.arguments(posonlyargs=[ast.arg("x")], kwonlyargs=[ast.arg('y')])
        self.assertEqual(ast.dump(node, annotate_fields=False),
            "arguments([arg('x')], kwonlyargs=[arg('y')])",
        )
        node = ast.arguments(args=[ast.arg("x")], kwonlyargs=[ast.arg('y')])
        self.assertEqual(ast.dump(node, annotate_fields=False),
            "arguments([], [arg('x')], kwonlyargs=[arg('y')])",
        )
        node = ast.arguments()
        self.assertEqual(ast.dump(node, annotate_fields=False),
            "arguments()",
        )
        # Classes:
        node = ast.ClassDef(
            'T',
            [],
            [ast.keyword('a', ast.Constant(None))],
            [],
            [ast.Name('dataclass', ctx=ast.Load())],
        )
        self.assertEqual(ast.dump(node),
            "ClassDef(name='T', keywords=[keyword(arg='a', value=Constant(value=None))], decorator_list=[Name(id='dataclass', ctx=Load())])",
        )
        self.assertEqual(ast.dump(node, annotate_fields=False),
            "ClassDef('T', [], [keyword('a', Constant(None))], [], [Name('dataclass', Load())])",
        )

    def test_dump_show_empty(self):
        def check_node(node, empty, full, **kwargs):
            with self.subTest(show_empty=False):
                self.assertEqual(
                    ast.dump(node, show_empty=False, **kwargs),
                    empty,
                )
            with self.subTest(show_empty=True):
                self.assertEqual(
                    ast.dump(node, show_empty=True, **kwargs),
                    full,
                )

        def check_text(code, empty, full, **kwargs):
            check_node(ast.parse(code), empty, full, **kwargs)

        check_node(
            ast.arguments(),
            empty="arguments()",
            full="arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[])",
        )

        check_node(
            # Corner case: there are no real `Name` instances with `id=''`:
            ast.Name(id='', ctx=ast.Load()),
            empty="Name(id='', ctx=Load())",
            full="Name(id='', ctx=Load())",
        )

        check_node(
            ast.MatchSingleton(value=None),
            empty="MatchSingleton(value=None)",
            full="MatchSingleton(value=None)",
        )

        check_node(
            ast.Constant(value=None),
            empty="Constant(value=None)",
            full="Constant(value=None)",
        )

        check_node(
            ast.Constant(value=''),
            empty="Constant(value='')",
            full="Constant(value='')",
        )

        check_text(
            "def a(b: int = 0, *, c): ...",
            empty="Module(body=[FunctionDef(name='a', args=arguments(args=[arg(arg='b', annotation=Name(id='int', ctx=Load()))], kwonlyargs=[arg(arg='c')], kw_defaults=[None], defaults=[Constant(value=0)]), body=[Expr(value=Constant(value=Ellipsis))])])",
            full="Module(body=[FunctionDef(name='a', args=arguments(posonlyargs=[], args=[arg(arg='b', annotation=Name(id='int', ctx=Load()))], kwonlyargs=[arg(arg='c')], kw_defaults=[None], defaults=[Constant(value=0)]), body=[Expr(value=Constant(value=Ellipsis))], decorator_list=[], type_params=[])], type_ignores=[])",
        )

        check_text(
            "def a(b: int = 0, *, c): ...",
            empty="Module(body=[FunctionDef(name='a', args=arguments(args=[arg(arg='b', annotation=Name(id='int', ctx=Load(), lineno=1, col_offset=9, end_lineno=1, end_col_offset=12), lineno=1, col_offset=6, end_lineno=1, end_col_offset=12)], kwonlyargs=[arg(arg='c', lineno=1, col_offset=21, end_lineno=1, end_col_offset=22)], kw_defaults=[None], defaults=[Constant(value=0, lineno=1, col_offset=15, end_lineno=1, end_col_offset=16)]), body=[Expr(value=Constant(value=Ellipsis, lineno=1, col_offset=25, end_lineno=1, end_col_offset=28), lineno=1, col_offset=25, end_lineno=1, end_col_offset=28)], lineno=1, col_offset=0, end_lineno=1, end_col_offset=28)])",
            full="Module(body=[FunctionDef(name='a', args=arguments(posonlyargs=[], args=[arg(arg='b', annotation=Name(id='int', ctx=Load(), lineno=1, col_offset=9, end_lineno=1, end_col_offset=12), lineno=1, col_offset=6, end_lineno=1, end_col_offset=12)], kwonlyargs=[arg(arg='c', lineno=1, col_offset=21, end_lineno=1, end_col_offset=22)], kw_defaults=[None], defaults=[Constant(value=0, lineno=1, col_offset=15, end_lineno=1, end_col_offset=16)]), body=[Expr(value=Constant(value=Ellipsis, lineno=1, col_offset=25, end_lineno=1, end_col_offset=28), lineno=1, col_offset=25, end_lineno=1, end_col_offset=28)], decorator_list=[], type_params=[], lineno=1, col_offset=0, end_lineno=1, end_col_offset=28)], type_ignores=[])",
            include_attributes=True,
        )

        check_text(
            'spam(eggs, "and cheese")',
            empty="Module(body=[Expr(value=Call(func=Name(id='spam', ctx=Load()), args=[Name(id='eggs', ctx=Load()), Constant(value='and cheese')]))])",
            full="Module(body=[Expr(value=Call(func=Name(id='spam', ctx=Load()), args=[Name(id='eggs', ctx=Load()), Constant(value='and cheese')], keywords=[]))], type_ignores=[])",
        )

        check_text(
            'spam(eggs, text="and cheese")',
            empty="Module(body=[Expr(value=Call(func=Name(id='spam', ctx=Load()), args=[Name(id='eggs', ctx=Load())], keywords=[keyword(arg='text', value=Constant(value='and cheese'))]))])",
            full="Module(body=[Expr(value=Call(func=Name(id='spam', ctx=Load()), args=[Name(id='eggs', ctx=Load())], keywords=[keyword(arg='text', value=Constant(value='and cheese'))]))], type_ignores=[])",
        )

        check_text(
            "import _ast as ast; from module import sub",
            empty="Module(body=[Import(names=[alias(name='_ast', asname='ast')]), ImportFrom(module='module', names=[alias(name='sub')], level=0)])",
            full="Module(body=[Import(names=[alias(name='_ast', asname='ast')]), ImportFrom(module='module', names=[alias(name='sub')], level=0)], type_ignores=[])",
        )

    def test_copy_location(self):
        src = ast.parse('1 + 1', mode='eval')
        src.body.right = ast.copy_location(ast.Constant(2), src.body.right)
        self.assertEqual(ast.dump(src, include_attributes=True),
            'Expression(body=BinOp(left=Constant(value=1, lineno=1, col_offset=0, '
            'end_lineno=1, end_col_offset=1), op=Add(), right=Constant(value=2, '
            'lineno=1, col_offset=4, end_lineno=1, end_col_offset=5), lineno=1, '
            'col_offset=0, end_lineno=1, end_col_offset=5))'
        )
        func = ast.Name('spam', ast.Load())
        src = ast.Call(col_offset=1, lineno=1, end_lineno=1, end_col_offset=1, func=func)
        new = ast.copy_location(src, ast.Call(col_offset=None, lineno=None, func=func))
        self.assertIsNone(new.end_lineno)
        self.assertIsNone(new.end_col_offset)
        self.assertEqual(new.lineno, 1)
        self.assertEqual(new.col_offset, 1)

    def test_fix_missing_locations(self):
        src = ast.parse('write("spam")')
        src.body.append(ast.Expr(ast.Call(ast.Name('spam', ast.Load()),
                                          [ast.Constant('eggs')], [])))
        self.assertEqual(src, ast.fix_missing_locations(src))
        self.maxDiff = None
        self.assertEqual(ast.dump(src, include_attributes=True),
            "Module(body=[Expr(value=Call(func=Name(id='write', ctx=Load(), "
            "lineno=1, col_offset=0, end_lineno=1, end_col_offset=5), "
            "args=[Constant(value='spam', lineno=1, col_offset=6, end_lineno=1, "
            "end_col_offset=12)], lineno=1, col_offset=0, end_lineno=1, "
            "end_col_offset=13), lineno=1, col_offset=0, end_lineno=1, "
            "end_col_offset=13), Expr(value=Call(func=Name(id='spam', ctx=Load(), "
            "lineno=1, col_offset=0, end_lineno=1, end_col_offset=0), "
            "args=[Constant(value='eggs', lineno=1, col_offset=0, end_lineno=1, "
            "end_col_offset=0)], lineno=1, col_offset=0, end_lineno=1, "
            "end_col_offset=0), lineno=1, col_offset=0, end_lineno=1, end_col_offset=0)])"
        )

    def test_increment_lineno(self):
        src = ast.parse('1 + 1', mode='eval')
        self.assertEqual(ast.increment_lineno(src, n=3), src)
        self.assertEqual(ast.dump(src, include_attributes=True),
            'Expression(body=BinOp(left=Constant(value=1, lineno=4, col_offset=0, '
            'end_lineno=4, end_col_offset=1), op=Add(), right=Constant(value=1, '
            'lineno=4, col_offset=4, end_lineno=4, end_col_offset=5), lineno=4, '
            'col_offset=0, end_lineno=4, end_col_offset=5))'
        )
        # issue10869: do not increment lineno of root twice
        src = ast.parse('1 + 1', mode='eval')
        self.assertEqual(ast.increment_lineno(src.body, n=3), src.body)
        self.assertEqual(ast.dump(src, include_attributes=True),
            'Expression(body=BinOp(left=Constant(value=1, lineno=4, col_offset=0, '
            'end_lineno=4, end_col_offset=1), op=Add(), right=Constant(value=1, '
            'lineno=4, col_offset=4, end_lineno=4, end_col_offset=5), lineno=4, '
            'col_offset=0, end_lineno=4, end_col_offset=5))'
        )
        src = ast.Call(
            func=ast.Name("test", ast.Load()), args=[], keywords=[], lineno=1
        )
        self.assertEqual(ast.increment_lineno(src).lineno, 2)
        self.assertIsNone(ast.increment_lineno(src).end_lineno)

    def test_increment_lineno_on_module(self):
        src = ast.parse(dedent("""\
        a = 1
        b = 2 # type: ignore
        c = 3
        d = 4 # type: ignore@tag
        """), type_comments=True)
        ast.increment_lineno(src, n=5)
        self.assertEqual(src.type_ignores[0].lineno, 7)
        self.assertEqual(src.type_ignores[1].lineno, 9)
        self.assertEqual(src.type_ignores[1].tag, '@tag')

    def test_iter_fields(self):
        node = ast.parse('foo()', mode='eval')
        d = dict(ast.iter_fields(node.body))
        self.assertEqual(d.pop('func').id, 'foo')
        self.assertEqual(d, {'keywords': [], 'args': []})

    def test_iter_child_nodes(self):
        node = ast.parse("spam(23, 42, eggs='leek')", mode='eval')
        self.assertEqual(len(list(ast.iter_child_nodes(node.body))), 4)
        iterator = ast.iter_child_nodes(node.body)
        self.assertEqual(next(iterator).id, 'spam')
        self.assertEqual(next(iterator).value, 23)
        self.assertEqual(next(iterator).value, 42)
        self.assertEqual(ast.dump(next(iterator)),
            "keyword(arg='eggs', value=Constant(value='leek'))"
        )

    def test_get_docstring(self):
        node = ast.parse('"""line one\n  line two"""')
        self.assertEqual(ast.get_docstring(node),
                         'line one\nline two')

        node = ast.parse('class foo:\n  """line one\n  line two"""')
        self.assertEqual(ast.get_docstring(node.body[0]),
                         'line one\nline two')

        node = ast.parse('def foo():\n  """line one\n  line two"""')
        self.assertEqual(ast.get_docstring(node.body[0]),
                         'line one\nline two')

        node = ast.parse('async def foo():\n  """spam\n  ham"""')
        self.assertEqual(ast.get_docstring(node.body[0]), 'spam\nham')

    def test_get_docstring_none(self):
        self.assertIsNone(ast.get_docstring(ast.parse('')))
        node = ast.parse('x = "not docstring"')
        self.assertIsNone(ast.get_docstring(node))
        node = ast.parse('def foo():\n  pass')
        self.assertIsNone(ast.get_docstring(node))

        node = ast.parse('class foo:\n  pass')
        self.assertIsNone(ast.get_docstring(node.body[0]))
        node = ast.parse('class foo:\n  x = "not docstring"')
        self.assertIsNone(ast.get_docstring(node.body[0]))
        node = ast.parse('class foo:\n  def bar(self): pass')
        self.assertIsNone(ast.get_docstring(node.body[0]))

        node = ast.parse('def foo():\n  pass')
        self.assertIsNone(ast.get_docstring(node.body[0]))
        node = ast.parse('def foo():\n  x = "not docstring"')
        self.assertIsNone(ast.get_docstring(node.body[0]))

        node = ast.parse('async def foo():\n  pass')
        self.assertIsNone(ast.get_docstring(node.body[0]))
        node = ast.parse('async def foo():\n  x = "not docstring"')
        self.assertIsNone(ast.get_docstring(node.body[0]))

    def test_multi_line_docstring_col_offset_and_lineno_issue16806(self):
        node = ast.parse(
            '"""line one\nline two"""\n\n'
            'def foo():\n  """line one\n  line two"""\n\n'
            '  def bar():\n    """line one\n    line two"""\n'
            '  """line one\n  line two"""\n'
            '"""line one\nline two"""\n\n'
        )
        self.assertEqual(node.body[0].col_offset, 0)
        self.assertEqual(node.body[0].lineno, 1)
        self.assertEqual(node.body[1].body[0].col_offset, 2)
        self.assertEqual(node.body[1].body[0].lineno, 5)
        self.assertEqual(node.body[1].body[1].body[0].col_offset, 4)
        self.assertEqual(node.body[1].body[1].body[0].lineno, 9)
        self.assertEqual(node.body[1].body[2].col_offset, 2)
        self.assertEqual(node.body[1].body[2].lineno, 11)
        self.assertEqual(node.body[2].col_offset, 0)
        self.assertEqual(node.body[2].lineno, 13)

    def test_elif_stmt_start_position(self):
        node = ast.parse('if a:\n    pass\nelif b:\n    pass\n')
        elif_stmt = node.body[0].orelse[0]
        self.assertEqual(elif_stmt.lineno, 3)
        self.assertEqual(elif_stmt.col_offset, 0)

    def test_elif_stmt_start_position_with_else(self):
        node = ast.parse('if a:\n    pass\nelif b:\n    pass\nelse:\n    pass\n')
        elif_stmt = node.body[0].orelse[0]
        self.assertEqual(elif_stmt.lineno, 3)
        self.assertEqual(elif_stmt.col_offset, 0)

    def test_starred_expr_end_position_within_call(self):
        node = ast.parse('f(*[0, 1])')
        starred_expr = node.body[0].value.args[0]
        self.assertEqual(starred_expr.end_lineno, 1)
        self.assertEqual(starred_expr.end_col_offset, 9)

    def test_literal_eval(self):
        self.assertEqual(ast.literal_eval('[1, 2, 3]'), [1, 2, 3])
        self.assertEqual(ast.literal_eval('{"foo": 42}'), {"foo": 42})
        self.assertEqual(ast.literal_eval('(True, False, None)'), (True, False, None))
        self.assertEqual(ast.literal_eval('{1, 2, 3}'), {1, 2, 3})
        self.assertEqual(ast.literal_eval('b"hi"'), b"hi")
        self.assertEqual(ast.literal_eval('set()'), set())
        self.assertRaises(ValueError, ast.literal_eval, 'foo()')
        self.assertEqual(ast.literal_eval('6'), 6)
        self.assertEqual(ast.literal_eval('+6'), 6)
        self.assertEqual(ast.literal_eval('-6'), -6)
        self.assertEqual(ast.literal_eval('3.25'), 3.25)
        self.assertEqual(ast.literal_eval('+3.25'), 3.25)
        self.assertEqual(ast.literal_eval('-3.25'), -3.25)
        self.assertEqual(repr(ast.literal_eval('-0.0')), '-0.0')
        self.assertRaises(ValueError, ast.literal_eval, '++6')
        self.assertRaises(ValueError, ast.literal_eval, '+True')
        self.assertRaises(ValueError, ast.literal_eval, '2+3')

    def test_literal_eval_str_int_limit(self):
        with support.adjust_int_max_str_digits(4000):
            ast.literal_eval('3'*4000)  # no error
            with self.assertRaises(SyntaxError) as err_ctx:
                ast.literal_eval('3'*4001)
            self.assertIn('Exceeds the limit ', str(err_ctx.exception))
            self.assertIn(' Consider hexadecimal ', str(err_ctx.exception))

    def test_literal_eval_complex(self):
        # Issue #4907
        self.assertEqual(ast.literal_eval('6j'), 6j)
        self.assertEqual(ast.literal_eval('-6j'), -6j)
        self.assertEqual(ast.literal_eval('6.75j'), 6.75j)
        self.assertEqual(ast.literal_eval('-6.75j'), -6.75j)
        self.assertEqual(ast.literal_eval('3+6j'), 3+6j)
        self.assertEqual(ast.literal_eval('-3+6j'), -3+6j)
        self.assertEqual(ast.literal_eval('3-6j'), 3-6j)
        self.assertEqual(ast.literal_eval('-3-6j'), -3-6j)
        self.assertEqual(ast.literal_eval('3.25+6.75j'), 3.25+6.75j)
        self.assertEqual(ast.literal_eval('-3.25+6.75j'), -3.25+6.75j)
        self.assertEqual(ast.literal_eval('3.25-6.75j'), 3.25-6.75j)
        self.assertEqual(ast.literal_eval('-3.25-6.75j'), -3.25-6.75j)
        self.assertEqual(ast.literal_eval('(3+6j)'), 3+6j)
        self.assertRaises(ValueError, ast.literal_eval, '-6j+3')
        self.assertRaises(ValueError, ast.literal_eval, '-6j+3j')
        self.assertRaises(ValueError, ast.literal_eval, '3+-6j')
        self.assertRaises(ValueError, ast.literal_eval, '3+(0+6j)')
        self.assertRaises(ValueError, ast.literal_eval, '-(3+6j)')

    def test_literal_eval_malformed_dict_nodes(self):
        malformed = ast.Dict(keys=[ast.Constant(1), ast.Constant(2)], values=[ast.Constant(3)])
        self.assertRaises(ValueError, ast.literal_eval, malformed)
        malformed = ast.Dict(keys=[ast.Constant(1)], values=[ast.Constant(2), ast.Constant(3)])
        self.assertRaises(ValueError, ast.literal_eval, malformed)

    def test_literal_eval_trailing_ws(self):
        self.assertEqual(ast.literal_eval("    -1"), -1)
        self.assertEqual(ast.literal_eval("\t\t-1"), -1)
        self.assertEqual(ast.literal_eval(" \t -1"), -1)
        self.assertRaises(IndentationError, ast.literal_eval, "\n -1")

    def test_literal_eval_malformed_lineno(self):
        msg = r'malformed node or string on line 3:'
        with self.assertRaisesRegex(ValueError, msg):
            ast.literal_eval("{'a': 1,\n'b':2,\n'c':++3,\n'd':4}")

        node = ast.UnaryOp(
            ast.UAdd(), ast.UnaryOp(ast.UAdd(), ast.Constant(6)))
        self.assertIsNone(getattr(node, 'lineno', None))
        msg = r'malformed node or string:'
        with self.assertRaisesRegex(ValueError, msg):
            ast.literal_eval(node)

    def test_literal_eval_syntax_errors(self):
        with self.assertRaisesRegex(SyntaxError, "unexpected indent"):
            ast.literal_eval(r'''
                \
                (\
            \ ''')

    def test_bad_integer(self):
        # issue13436: Bad error message with invalid numeric values
        body = [ast.ImportFrom(module='time',
                               names=[ast.alias(name='sleep')],
                               level=None,
                               lineno=None, col_offset=None)]
        mod = ast.Module(body, [])
        with self.assertRaises(ValueError) as cm:
            compile(mod, 'test', 'exec')
        self.assertIn("invalid integer value: None", str(cm.exception))

    def test_level_as_none(self):
        body = [ast.ImportFrom(module='time',
                               names=[ast.alias(name='sleep',
                                                lineno=0, col_offset=0)],
                               level=None,
                               lineno=0, col_offset=0)]
        mod = ast.Module(body, [])
        code = compile(mod, 'test', 'exec')
        ns = {}
        exec(code, ns)
        self.assertIn('sleep', ns)

    def test_recursion_direct(self):
        e = ast.UnaryOp(op=ast.Not(), lineno=0, col_offset=0, operand=ast.Constant(1))
        e.operand = e
        with self.assertRaises(RecursionError):
            with support.infinite_recursion():
                compile(ast.Expression(e), "<test>", "eval")

    def test_recursion_indirect(self):
        e = ast.UnaryOp(op=ast.Not(), lineno=0, col_offset=0, operand=ast.Constant(1))
        f = ast.UnaryOp(op=ast.Not(), lineno=0, col_offset=0, operand=ast.Constant(1))
        e.operand = f
        f.operand = e
        with self.assertRaises(RecursionError):
            with support.infinite_recursion():
                compile(ast.Expression(e), "<test>", "eval")


class ASTValidatorTests(unittest.TestCase):

    def mod(self, mod, msg=None, mode="exec", *, exc=ValueError):
        mod.lineno = mod.col_offset = 0
        ast.fix_missing_locations(mod)
        if msg is None:
            compile(mod, "<test>", mode)
        else:
            with self.assertRaises(exc) as cm:
                compile(mod, "<test>", mode)
            self.assertIn(msg, str(cm.exception))

    def expr(self, node, msg=None, *, exc=ValueError):
        mod = ast.Module([ast.Expr(node)], [])
        self.mod(mod, msg, exc=exc)

    def stmt(self, stmt, msg=None):
        mod = ast.Module([stmt], [])
        self.mod(mod, msg)

    def test_module(self):
        m = ast.Interactive([ast.Expr(ast.Name("x", ast.Store()))])
        self.mod(m, "must have Load context", "single")
        m = ast.Expression(ast.Name("x", ast.Store()))
        self.mod(m, "must have Load context", "eval")

    def _check_arguments(self, fac, check):
        def arguments(args=None, posonlyargs=None, vararg=None,
                      kwonlyargs=None, kwarg=None,
                      defaults=None, kw_defaults=None):
            if args is None:
                args = []
            if posonlyargs is None:
                posonlyargs = []
            if kwonlyargs is None:
                kwonlyargs = []
            if defaults is None:
                defaults = []
            if kw_defaults is None:
                kw_defaults = []
            args = ast.arguments(args, posonlyargs, vararg, kwonlyargs,
                                 kw_defaults, kwarg, defaults)
            return fac(args)
        args = [ast.arg("x", ast.Name("x", ast.Store()))]
        check(arguments(args=args), "must have Load context")
        check(arguments(posonlyargs=args), "must have Load context")
        check(arguments(kwonlyargs=args), "must have Load context")
        check(arguments(defaults=[ast.Constant(3)]),
                       "more positional defaults than args")
        check(arguments(kw_defaults=[ast.Constant(4)]),
                       "length of kwonlyargs is not the same as kw_defaults")
        args = [ast.arg("x", ast.Name("x", ast.Load()))]
        check(arguments(args=args, defaults=[ast.Name("x", ast.Store())]),
                       "must have Load context")
        args = [ast.arg("a", ast.Name("x", ast.Load())),
                ast.arg("b", ast.Name("y", ast.Load()))]
        check(arguments(kwonlyargs=args,
                          kw_defaults=[None, ast.Name("x", ast.Store())]),
                          "must have Load context")

    def test_funcdef(self):
        a = ast.arguments([], [], None, [], [], None, [])
        f = ast.FunctionDef("x", a, [], [], None, None, [])
        self.stmt(f, "empty body on FunctionDef")
        f = ast.FunctionDef("x", a, [ast.Pass()], [ast.Name("x", ast.Store())], None, None, [])
        self.stmt(f, "must have Load context")
        f = ast.FunctionDef("x", a, [ast.Pass()], [],
                            ast.Name("x", ast.Store()), None, [])
        self.stmt(f, "must have Load context")
        f = ast.FunctionDef("x", ast.arguments(), [ast.Pass()])
        self.stmt(f)
        def fac(args):
            return ast.FunctionDef("x", args, [ast.Pass()], [], None, None, [])
        self._check_arguments(fac, self.stmt)

    def test_funcdef_pattern_matching(self):
        # gh-104799: New fields on FunctionDef should be added at the end
        def matcher(node):
            match node:
                case ast.FunctionDef("foo", ast.arguments(args=[ast.arg("bar")]),
                                     [ast.Pass()],
                                     [ast.Name("capybara", ast.Load())],
                                     ast.Name("pacarana", ast.Load())):
                    return True
                case _:
                    return False

        code = """
            @capybara
            def foo(bar) -> pacarana:
                pass
        """
        source = ast.parse(textwrap.dedent(code))
        funcdef = source.body[0]
        self.assertIsInstance(funcdef, ast.FunctionDef)
        self.assertTrue(matcher(funcdef))

    def test_classdef(self):
        def cls(bases=None, keywords=None, body=None, decorator_list=None, type_params=None):
            if bases is None:
                bases = []
            if keywords is None:
                keywords = []
            if body is None:
                body = [ast.Pass()]
            if decorator_list is None:
                decorator_list = []
            if type_params is None:
                type_params = []
            return ast.ClassDef("myclass", bases, keywords,
                                body, decorator_list, type_params)
        self.stmt(cls(bases=[ast.Name("x", ast.Store())]),
                  "must have Load context")
        self.stmt(cls(keywords=[ast.keyword("x", ast.Name("x", ast.Store()))]),
                  "must have Load context")
        self.stmt(cls(body=[]), "empty body on ClassDef")
        self.stmt(cls(body=[None]), "None disallowed")
        self.stmt(cls(decorator_list=[ast.Name("x", ast.Store())]),
                  "must have Load context")

    def test_delete(self):
        self.stmt(ast.Delete([]), "empty targets on Delete")
        self.stmt(ast.Delete([None]), "None disallowed")
        self.stmt(ast.Delete([ast.Name("x", ast.Load())]),
                  "must have Del context")

    def test_assign(self):
        self.stmt(ast.Assign([], ast.Constant(3)), "empty targets on Assign")
        self.stmt(ast.Assign([None], ast.Constant(3)), "None disallowed")
        self.stmt(ast.Assign([ast.Name("x", ast.Load())], ast.Constant(3)),
                  "must have Store context")
        self.stmt(ast.Assign([ast.Name("x", ast.Store())],
                                ast.Name("y", ast.Store())),
                  "must have Load context")

    def test_augassign(self):
        aug = ast.AugAssign(ast.Name("x", ast.Load()), ast.Add(),
                            ast.Name("y", ast.Load()))
        self.stmt(aug, "must have Store context")
        aug = ast.AugAssign(ast.Name("x", ast.Store()), ast.Add(),
                            ast.Name("y", ast.Store()))
        self.stmt(aug, "must have Load context")

    def test_for(self):
        x = ast.Name("x", ast.Store())
        y = ast.Name("y", ast.Load())
        p = ast.Pass()
        self.stmt(ast.For(x, y, [], []), "empty body on For")
        self.stmt(ast.For(ast.Name("x", ast.Load()), y, [p], []),
                  "must have Store context")
        self.stmt(ast.For(x, ast.Name("y", ast.Store()), [p], []),
                  "must have Load context")
        e = ast.Expr(ast.Name("x", ast.Store()))
        self.stmt(ast.For(x, y, [e], []), "must have Load context")
        self.stmt(ast.For(x, y, [p], [e]), "must have Load context")

    def test_while(self):
        self.stmt(ast.While(ast.Constant(3), [], []), "empty body on While")
        self.stmt(ast.While(ast.Name("x", ast.Store()), [ast.Pass()], []),
                  "must have Load context")
        self.stmt(ast.While(ast.Constant(3), [ast.Pass()],
                             [ast.Expr(ast.Name("x", ast.Store()))]),
                             "must have Load context")

    def test_if(self):
        self.stmt(ast.If(ast.Constant(3), [], []), "empty body on If")
        i = ast.If(ast.Name("x", ast.Store()), [ast.Pass()], [])
        self.stmt(i, "must have Load context")
        i = ast.If(ast.Constant(3), [ast.Expr(ast.Name("x", ast.Store()))], [])
        self.stmt(i, "must have Load context")
        i = ast.If(ast.Constant(3), [ast.Pass()],
                   [ast.Expr(ast.Name("x", ast.Store()))])
        self.stmt(i, "must have Load context")

    def test_with(self):
        p = ast.Pass()
        self.stmt(ast.With([], [p]), "empty items on With")
        i = ast.withitem(ast.Constant(3), None)
        self.stmt(ast.With([i], []), "empty body on With")
        i = ast.withitem(ast.Name("x", ast.Store()), None)
        self.stmt(ast.With([i], [p]), "must have Load context")
        i = ast.withitem(ast.Constant(3), ast.Name("x", ast.Load()))
        self.stmt(ast.With([i], [p]), "must have Store context")

    def test_raise(self):
        r = ast.Raise(None, ast.Constant(3))
        self.stmt(r, "Raise with cause but no exception")
        r = ast.Raise(ast.Name("x", ast.Store()), None)
        self.stmt(r, "must have Load context")
        r = ast.Raise(ast.Constant(4), ast.Name("x", ast.Store()))
        self.stmt(r, "must have Load context")

    def test_try(self):
        p = ast.Pass()
        t = ast.Try([], [], [], [p])
        self.stmt(t, "empty body on Try")
        t = ast.Try([ast.Expr(ast.Name("x", ast.Store()))], [], [], [p])
        self.stmt(t, "must have Load context")
        t = ast.Try([p], [], [], [])
        self.stmt(t, "Try has neither except handlers nor finalbody")
        t = ast.Try([p], [], [p], [p])
        self.stmt(t, "Try has orelse but no except handlers")
        t = ast.Try([p], [ast.ExceptHandler(None, "x", [])], [], [])
        self.stmt(t, "empty body on ExceptHandler")
        e = [ast.ExceptHandler(ast.Name("x", ast.Store()), "y", [p])]
        self.stmt(ast.Try([p], e, [], []), "must have Load context")
        e = [ast.ExceptHandler(None, "x", [p])]
        t = ast.Try([p], e, [ast.Expr(ast.Name("x", ast.Store()))], [p])
        self.stmt(t, "must have Load context")
        t = ast.Try([p], e, [p], [ast.Expr(ast.Name("x", ast.Store()))])
        self.stmt(t, "must have Load context")

    def test_try_star(self):
        p = ast.Pass()
        t = ast.TryStar([], [], [], [p])
        self.stmt(t, "empty body on TryStar")
        t = ast.TryStar([ast.Expr(ast.Name("x", ast.Store()))], [], [], [p])
        self.stmt(t, "must have Load context")
        t = ast.TryStar([p], [], [], [])
        self.stmt(t, "TryStar has neither except handlers nor finalbody")
        t = ast.TryStar([p], [], [p], [p])
        self.stmt(t, "TryStar has orelse but no except handlers")
        t = ast.TryStar([p], [ast.ExceptHandler(None, "x", [])], [], [])
        self.stmt(t, "empty body on ExceptHandler")
        e = [ast.ExceptHandler(ast.Name("x", ast.Store()), "y", [p])]
        self.stmt(ast.TryStar([p], e, [], []), "must have Load context")
        e = [ast.ExceptHandler(None, "x", [p])]
        t = ast.TryStar([p], e, [ast.Expr(ast.Name("x", ast.Store()))], [p])
        self.stmt(t, "must have Load context")
        t = ast.TryStar([p], e, [p], [ast.Expr(ast.Name("x", ast.Store()))])
        self.stmt(t, "must have Load context")

    def test_assert(self):
        self.stmt(ast.Assert(ast.Name("x", ast.Store()), None),
                  "must have Load context")
        assrt = ast.Assert(ast.Name("x", ast.Load()),
                           ast.Name("y", ast.Store()))
        self.stmt(assrt, "must have Load context")

    def test_import(self):
        self.stmt(ast.Import([]), "empty names on Import")

    def test_importfrom(self):
        imp = ast.ImportFrom(None, [ast.alias("x", None)], -42)
        self.stmt(imp, "Negative ImportFrom level")
        self.stmt(ast.ImportFrom(None, [], 0), "empty names on ImportFrom")

    def test_global(self):
        self.stmt(ast.Global([]), "empty names on Global")

    def test_nonlocal(self):
        self.stmt(ast.Nonlocal([]), "empty names on Nonlocal")

    def test_expr(self):
        e = ast.Expr(ast.Name("x", ast.Store()))
        self.stmt(e, "must have Load context")

    def test_boolop(self):
        b = ast.BoolOp(ast.And(), [])
        self.expr(b, "less than 2 values")
        b = ast.BoolOp(ast.And(), [ast.Constant(3)])
        self.expr(b, "less than 2 values")
        b = ast.BoolOp(ast.And(), [ast.Constant(4), None])
        self.expr(b, "None disallowed")
        b = ast.BoolOp(ast.And(), [ast.Constant(4), ast.Name("x", ast.Store())])
        self.expr(b, "must have Load context")

    def test_unaryop(self):
        u = ast.UnaryOp(ast.Not(), ast.Name("x", ast.Store()))
        self.expr(u, "must have Load context")

    def test_lambda(self):
        a = ast.arguments([], [], None, [], [], None, [])
        self.expr(ast.Lambda(a, ast.Name("x", ast.Store())),
                  "must have Load context")
        def fac(args):
            return ast.Lambda(args, ast.Name("x", ast.Load()))
        self._check_arguments(fac, self.expr)

    def test_ifexp(self):
        l = ast.Name("x", ast.Load())
        s = ast.Name("y", ast.Store())
        for args in (s, l, l), (l, s, l), (l, l, s):
            self.expr(ast.IfExp(*args), "must have Load context")

    def test_dict(self):
        d = ast.Dict([], [ast.Name("x", ast.Load())])
        self.expr(d, "same number of keys as values")
        d = ast.Dict([ast.Name("x", ast.Load())], [None])
        self.expr(d, "None disallowed")

    def test_set(self):
        self.expr(ast.Set([None]), "None disallowed")
        s = ast.Set([ast.Name("x", ast.Store())])
        self.expr(s, "must have Load context")

    def _check_comprehension(self, fac):
        self.expr(fac([]), "comprehension with no generators")
        g = ast.comprehension(ast.Name("x", ast.Load()),
                              ast.Name("x", ast.Load()), [], 0)
        self.expr(fac([g]), "must have Store context")
        g = ast.comprehension(ast.Name("x", ast.Store()),
                              ast.Name("x", ast.Store()), [], 0)
        self.expr(fac([g]), "must have Load context")
        x = ast.Name("x", ast.Store())
        y = ast.Name("y", ast.Load())
        g = ast.comprehension(x, y, [None], 0)
        self.expr(fac([g]), "None disallowed")
        g = ast.comprehension(x, y, [ast.Name("x", ast.Store())], 0)
        self.expr(fac([g]), "must have Load context")

    def _simple_comp(self, fac):
        g = ast.comprehension(ast.Name("x", ast.Store()),
                              ast.Name("x", ast.Load()), [], 0)
        self.expr(fac(ast.Name("x", ast.Store()), [g]),
                  "must have Load context")
        def wrap(gens):
            return fac(ast.Name("x", ast.Store()), gens)
        self._check_comprehension(wrap)

    def test_listcomp(self):
        self._simple_comp(ast.ListComp)

    def test_setcomp(self):
        self._simple_comp(ast.SetComp)

    def test_generatorexp(self):
        self._simple_comp(ast.GeneratorExp)

    def test_dictcomp(self):
        g = ast.comprehension(ast.Name("y", ast.Store()),
                              ast.Name("p", ast.Load()), [], 0)
        c = ast.DictComp(ast.Name("x", ast.Store()),
                         ast.Name("y", ast.Load()), [g])
        self.expr(c, "must have Load context")
        c = ast.DictComp(ast.Name("x", ast.Load()),
                         ast.Name("y", ast.Store()), [g])
        self.expr(c, "must have Load context")
        def factory(comps):
            k = ast.Name("x", ast.Load())
            v = ast.Name("y", ast.Load())
            return ast.DictComp(k, v, comps)
        self._check_comprehension(factory)

    def test_yield(self):
        self.expr(ast.Yield(ast.Name("x", ast.Store())), "must have Load")
        self.expr(ast.YieldFrom(ast.Name("x", ast.Store())), "must have Load")

    def test_compare(self):
        left = ast.Name("x", ast.Load())
        comp = ast.Compare(left, [ast.In()], [])
        self.expr(comp, "no comparators")
        comp = ast.Compare(left, [ast.In()], [ast.Constant(4), ast.Constant(5)])
        self.expr(comp, "different number of comparators and operands")
        comp = ast.Compare(ast.Constant("blah"), [ast.In()], [left])
        self.expr(comp)
        comp = ast.Compare(left, [ast.In()], [ast.Constant("blah")])
        self.expr(comp)

    def test_call(self):
        func = ast.Name("x", ast.Load())
        args = [ast.Name("y", ast.Load())]
        keywords = [ast.keyword("w", ast.Name("z", ast.Load()))]
        call = ast.Call(ast.Name("x", ast.Store()), args, keywords)
        self.expr(call, "must have Load context")
        call = ast.Call(func, [None], keywords)
        self.expr(call, "None disallowed")
        bad_keywords = [ast.keyword("w", ast.Name("z", ast.Store()))]
        call = ast.Call(func, args, bad_keywords)
        self.expr(call, "must have Load context")

    def test_attribute(self):
        attr = ast.Attribute(ast.Name("x", ast.Store()), "y", ast.Load())
        self.expr(attr, "must have Load context")

    def test_subscript(self):
        sub = ast.Subscript(ast.Name("x", ast.Store()), ast.Constant(3),
                            ast.Load())
        self.expr(sub, "must have Load context")
        x = ast.Name("x", ast.Load())
        sub = ast.Subscript(x, ast.Name("y", ast.Store()),
                            ast.Load())
        self.expr(sub, "must have Load context")
        s = ast.Name("x", ast.Store())
        for args in (s, None, None), (None, s, None), (None, None, s):
            sl = ast.Slice(*args)
            self.expr(ast.Subscript(x, sl, ast.Load()),
                      "must have Load context")
        sl = ast.Tuple([], ast.Load())
        self.expr(ast.Subscript(x, sl, ast.Load()))
        sl = ast.Tuple([s], ast.Load())
        self.expr(ast.Subscript(x, sl, ast.Load()), "must have Load context")

    def test_starred(self):
        left = ast.List([ast.Starred(ast.Name("x", ast.Load()), ast.Store())],
                        ast.Store())
        assign = ast.Assign([left], ast.Constant(4))
        self.stmt(assign, "must have Store context")

    def _sequence(self, fac):
        self.expr(fac([None], ast.Load()), "None disallowed")
        self.expr(fac([ast.Name("x", ast.Store())], ast.Load()),
                  "must have Load context")

    def test_list(self):
        self._sequence(ast.List)

    def test_tuple(self):
        self._sequence(ast.Tuple)

    @support.requires_resource('cpu')
    def test_stdlib_validates(self):
        for module in STDLIB_FILES:
            with self.subTest(module):
                fn = os.path.join(STDLIB, module)
                with open(fn, "r", encoding="utf-8") as fp:
                    source = fp.read()
                mod = ast.parse(source, fn)
                compile(mod, fn, "exec")
                mod2 = ast.parse(source, fn)
                self.assertTrue(ast.compare(mod, mod2))

    constant_1 = ast.Constant(1)
    pattern_1 = ast.MatchValue(constant_1)

    constant_x = ast.Constant('x')
    pattern_x = ast.MatchValue(constant_x)

    constant_true = ast.Constant(True)
    pattern_true = ast.MatchSingleton(True)

    name_carter = ast.Name('carter', ast.Load())

    _MATCH_PATTERNS = [
        ast.MatchValue(
            ast.Attribute(
                ast.Attribute(
                    ast.Name('x', ast.Store()),
                    'y', ast.Load()
                ),
                'z', ast.Load()
            )
        ),
        ast.MatchValue(
            ast.Attribute(
                ast.Attribute(
                    ast.Name('x', ast.Load()),
                    'y', ast.Store()
                ),
                'z', ast.Load()
            )
        ),
        ast.MatchValue(
            ast.Constant(...)
        ),
        ast.MatchValue(
            ast.Constant(True)
        ),
        ast.MatchValue(
            ast.Constant((1,2,3))
        ),
        ast.MatchSingleton('string'),
        ast.MatchSequence([
          ast.MatchSingleton('string')
        ]),
        ast.MatchSequence(
            [
                ast.MatchSequence(
                    [
                        ast.MatchSingleton('string')
                    ]
                )
            ]
        ),
        ast.MatchMapping(
            [constant_1, constant_true],
            [pattern_x]
        ),
        ast.MatchMapping(
            [constant_true, constant_1],
            [pattern_x, pattern_1],
            rest='True'
        ),
        ast.MatchMapping(
            [constant_true, ast.Starred(ast.Name('lol', ast.Load()), ast.Load())],
            [pattern_x, pattern_1],
            rest='legit'
        ),
        ast.MatchClass(
            ast.Attribute(
                ast.Attribute(
                    constant_x,
                    'y', ast.Load()),
                'z', ast.Load()),
            patterns=[], kwd_attrs=[], kwd_patterns=[]
        ),
        ast.MatchClass(
            name_carter,
            patterns=[],
            kwd_attrs=['True'],
            kwd_patterns=[pattern_1]
        ),
        ast.MatchClass(
            name_carter,
            patterns=[],
            kwd_attrs=[],
            kwd_patterns=[pattern_1]
        ),
        ast.MatchClass(
            name_carter,
            patterns=[ast.MatchSingleton('string')],
            kwd_attrs=[],
            kwd_patterns=[]
        ),
        ast.MatchClass(
            name_carter,
            patterns=[ast.MatchStar()],
            kwd_attrs=[],
            kwd_patterns=[]
        ),
        ast.MatchClass(
            name_carter,
            patterns=[],
            kwd_attrs=[],
            kwd_patterns=[ast.MatchStar()]
        ),
        ast.MatchClass(
            constant_true,  # invalid name
            patterns=[],
            kwd_attrs=['True'],
            kwd_patterns=[pattern_1]
        ),
        ast.MatchSequence(
            [
                ast.MatchStar("True")
            ]
        ),
        ast.MatchAs(
            name='False'
        ),
        ast.MatchOr(
            []
        ),
        ast.MatchOr(
            [pattern_1]
        ),
        ast.MatchOr(
            [pattern_1, pattern_x, ast.MatchSingleton('xxx')]
        ),
        ast.MatchAs(name="_"),
        ast.MatchStar(name="x"),
        ast.MatchSequence([ast.MatchStar("_")]),
        ast.MatchMapping([], [], rest="_"),
    ]

    def test_match_validation_pattern(self):
        name_x = ast.Name('x', ast.Load())
        for pattern in self._MATCH_PATTERNS:
            with self.subTest(ast.dump(pattern, indent=4)):
                node = ast.Match(
                    subject=name_x,
                    cases = [
                        ast.match_case(
                            pattern=pattern,
                            body = [ast.Pass()]
                        )
                    ]
                )
                node = ast.fix_missing_locations(node)
                module = ast.Module([node], [])
                with self.assertRaises(ValueError):
                    compile(module, "<test>", "exec")


class ConstantTests(unittest.TestCase):
    """Tests on the ast.Constant node type."""

    def compile_constant(self, value):
        tree = ast.parse("x = 123")

        node = tree.body[0].value
        new_node = ast.Constant(value=value)
        ast.copy_location(new_node, node)
        tree.body[0].value = new_node

        code = compile(tree, "<string>", "exec")

        ns = {}
        exec(code, ns)
        return ns['x']

    def test_validation(self):
        with self.assertRaises(TypeError) as cm:
            self.compile_constant([1, 2, 3])
        self.assertEqual(str(cm.exception),
                         "got an invalid type in Constant: list")

    def test_singletons(self):
        for const in (None, False, True, Ellipsis, b'', frozenset()):
            with self.subTest(const=const):
                value = self.compile_constant(const)
                self.assertIs(value, const)

    def test_values(self):
        nested_tuple = (1,)
        nested_frozenset = frozenset({1})
        for level in range(3):
            nested_tuple = (nested_tuple, 2)
            nested_frozenset = frozenset({nested_frozenset, 2})
        values = (123, 123.0, 123j,
                  "unicode", b'bytes',
                  tuple("tuple"), frozenset("frozenset"),
                  nested_tuple, nested_frozenset)
        for value in values:
            with self.subTest(value=value):
                result = self.compile_constant(value)
                self.assertEqual(result, value)

    def test_assign_to_constant(self):
        tree = ast.parse("x = 1")

        target = tree.body[0].targets[0]
        new_target = ast.Constant(value=1)
        ast.copy_location(new_target, target)
        tree.body[0].targets[0] = new_target

        with self.assertRaises(ValueError) as cm:
            compile(tree, "string", "exec")
        self.assertEqual(str(cm.exception),
                         "expression which can't be assigned "
                         "to in Store context")

    def test_get_docstring(self):
        tree = ast.parse("'docstring'\nx = 1")
        self.assertEqual(ast.get_docstring(tree), 'docstring')

    def get_load_const(self, tree):
        # Compile to bytecode, disassemble and get parameter of LOAD_CONST
        # instructions
        co = compile(tree, '<string>', 'exec')
        consts = []
        for instr in dis.get_instructions(co):
            if instr.opname == 'LOAD_CONST' or instr.opname == 'RETURN_CONST':
                consts.append(instr.argval)
        return consts

    @support.cpython_only
    def test_load_const(self):
        consts = [None,
                  True, False,
                  124,
                  2.0,
                  3j,
                  "unicode",
                  b'bytes',
                  (1, 2, 3)]

        code = '\n'.join(['x={!r}'.format(const) for const in consts])
        code += '\nx = ...'
        consts.extend((Ellipsis, None))

        tree = ast.parse(code)
        self.assertEqual(self.get_load_const(tree),
                         consts)

        # Replace expression nodes with constants
        for assign, const in zip(tree.body, consts):
            assert isinstance(assign, ast.Assign), ast.dump(assign)
            new_node = ast.Constant(value=const)
            ast.copy_location(new_node, assign.value)
            assign.value = new_node

        self.assertEqual(self.get_load_const(tree),
                         consts)

    def test_literal_eval(self):
        tree = ast.parse("1 + 2")
        binop = tree.body[0].value

        new_left = ast.Constant(value=10)
        ast.copy_location(new_left, binop.left)
        binop.left = new_left

        new_right = ast.Constant(value=20j)
        ast.copy_location(new_right, binop.right)
        binop.right = new_right

        self.assertEqual(ast.literal_eval(binop), 10+20j)

    def test_string_kind(self):
        c = ast.parse('"x"', mode='eval').body
        self.assertEqual(c.value, "x")
        self.assertEqual(c.kind, None)

        c = ast.parse('u"x"', mode='eval').body
        self.assertEqual(c.value, "x")
        self.assertEqual(c.kind, "u")

        c = ast.parse('r"x"', mode='eval').body
        self.assertEqual(c.value, "x")
        self.assertEqual(c.kind, None)

        c = ast.parse('b"x"', mode='eval').body
        self.assertEqual(c.value, b"x")
        self.assertEqual(c.kind, None)


class EndPositionTests(unittest.TestCase):
    """Tests for end position of AST nodes.

    Testing end positions of nodes requires a bit of extra care
    because of how LL parsers work.
    """
    def _check_end_pos(self, ast_node, end_lineno, end_col_offset):
        self.assertEqual(ast_node.end_lineno, end_lineno)
        self.assertEqual(ast_node.end_col_offset, end_col_offset)

    def _check_content(self, source, ast_node, content):
        self.assertEqual(ast.get_source_segment(source, ast_node), content)

    def _parse_value(self, s):
        # Use duck-typing to support both single expression
        # and a right hand side of an assignment statement.
        return ast.parse(s).body[0].value

    def test_lambda(self):
        s = 'lambda x, *y: None'
        lam = self._parse_value(s)
        self._check_content(s, lam.body, 'None')
        self._check_content(s, lam.args.args[0], 'x')
        self._check_content(s, lam.args.vararg, 'y')

    def test_func_def(self):
        s = dedent('''
            def func(x: int,
                     *args: str,
                     z: float = 0,
                     **kwargs: Any) -> bool:
                return True
            ''').strip()
        fdef = ast.parse(s).body[0]
        self._check_end_pos(fdef, 5, 15)
        self._check_content(s, fdef.body[0], 'return True')
        self._check_content(s, fdef.args.args[0], 'x: int')
        self._check_content(s, fdef.args.args[0].annotation, 'int')
        self._check_content(s, fdef.args.kwarg, 'kwargs: Any')
        self._check_content(s, fdef.args.kwarg.annotation, 'Any')

    def test_call(self):
        s = 'func(x, y=2, **kw)'
        call = self._parse_value(s)
        self._check_content(s, call.func, 'func')
        self._check_content(s, call.keywords[0].value, '2')
        self._check_content(s, call.keywords[1].value, 'kw')

    def test_call_noargs(self):
        s = 'x[0]()'
        call = self._parse_value(s)
        self._check_content(s, call.func, 'x[0]')
        self._check_end_pos(call, 1, 6)

    def test_class_def(self):
        s = dedent('''
            class C(A, B):
                x: int = 0
        ''').strip()
        cdef = ast.parse(s).body[0]
        self._check_end_pos(cdef, 2, 14)
        self._check_content(s, cdef.bases[1], 'B')
        self._check_content(s, cdef.body[0], 'x: int = 0')

    def test_class_kw(self):
        s = 'class S(metaclass=abc.ABCMeta): pass'
        cdef = ast.parse(s).body[0]
        self._check_content(s, cdef.keywords[0].value, 'abc.ABCMeta')

    def test_multi_line_str(self):
        s = dedent('''
            x = """Some multi-line text.

            It goes on starting from same indent."""
        ''').strip()
        assign = ast.parse(s).body[0]
        self._check_end_pos(assign, 3, 40)
        self._check_end_pos(assign.value, 3, 40)

    def test_continued_str(self):
        s = dedent('''
            x = "first part" \\
            "second part"
        ''').strip()
        assign = ast.parse(s).body[0]
        self._check_end_pos(assign, 2, 13)
        self._check_end_pos(assign.value, 2, 13)

    def test_suites(self):
        # We intentionally put these into the same string to check
        # that empty lines are not part of the suite.
        s = dedent('''
            while True:
                pass

            if one():
                x = None
            elif other():
                y = None
            else:
                z = None

            for x, y in stuff:
                assert True

            try:
                raise RuntimeError
            except TypeError as e:
                pass

            pass
        ''').strip()
        mod = ast.parse(s)
        while_loop = mod.body[0]
        if_stmt = mod.body[1]
        for_loop = mod.body[2]
        try_stmt = mod.body[3]
        pass_stmt = mod.body[4]

        self._check_end_pos(while_loop, 2, 8)
        self._check_end_pos(if_stmt, 9, 12)
        self._check_end_pos(for_loop, 12, 15)
        self._check_end_pos(try_stmt, 17, 8)
        self._check_end_pos(pass_stmt, 19, 4)

        self._check_content(s, while_loop.test, 'True')
        self._check_content(s, if_stmt.body[0], 'x = None')
        self._check_content(s, if_stmt.orelse[0].test, 'other()')
        self._check_content(s, for_loop.target, 'x, y')
        self._check_content(s, try_stmt.body[0], 'raise RuntimeError')
        self._check_content(s, try_stmt.handlers[0].type, 'TypeError')

    def test_fstring(self):
        s = 'x = f"abc {x + y} abc"'
        fstr = self._parse_value(s)
        binop = fstr.values[1].value
        self._check_content(s, binop, 'x + y')

    def test_fstring_multi_line(self):
        s = dedent('''
            f"""Some multi-line text.
            {
            arg_one
            +
            arg_two
            }
            It goes on..."""
        ''').strip()
        fstr = self._parse_value(s)
        binop = fstr.values[1].value
        self._check_end_pos(binop, 5, 7)
        self._check_content(s, binop.left, 'arg_one')
        self._check_content(s, binop.right, 'arg_two')

    def test_import_from_multi_line(self):
        s = dedent('''
            from x.y.z import (
                a, b, c as c
            )
        ''').strip()
        imp = ast.parse(s).body[0]
        self._check_end_pos(imp, 3, 1)
        self._check_end_pos(imp.names[2], 2, 16)

    def test_slices(self):
        s1 = 'f()[1, 2] [0]'
        s2 = 'x[ a.b: c.d]'
        sm = dedent('''
            x[ a.b: f () ,
               g () : c.d
              ]
        ''').strip()
        i1, i2, im = map(self._parse_value, (s1, s2, sm))
        self._check_content(s1, i1.value, 'f()[1, 2]')
        self._check_content(s1, i1.value.slice, '1, 2')
        self._check_content(s2, i2.slice.lower, 'a.b')
        self._check_content(s2, i2.slice.upper, 'c.d')
        self._check_content(sm, im.slice.elts[0].upper, 'f ()')
        self._check_content(sm, im.slice.elts[1].lower, 'g ()')
        self._check_end_pos(im, 3, 3)

    def test_binop(self):
        s = dedent('''
            (1 * 2 + (3 ) +
                 4
            )
        ''').strip()
        binop = self._parse_value(s)
        self._check_end_pos(binop, 2, 6)
        self._check_content(s, binop.right, '4')
        self._check_content(s, binop.left, '1 * 2 + (3 )')
        self._check_content(s, binop.left.right, '3')

    def test_boolop(self):
        s = dedent('''
            if (one_condition and
                    (other_condition or yet_another_one)):
                pass
        ''').strip()
        bop = ast.parse(s).body[0].test
        self._check_end_pos(bop, 2, 44)
        self._check_content(s, bop.values[1],
                            'other_condition or yet_another_one')

    def test_tuples(self):
        s1 = 'x = () ;'
        s2 = 'x = 1 , ;'
        s3 = 'x = (1 , 2 ) ;'
        sm = dedent('''
            x = (
                a, b,
            )
        ''').strip()
        t1, t2, t3, tm = map(self._parse_value, (s1, s2, s3, sm))
        self._check_content(s1, t1, '()')
        self._check_content(s2, t2, '1 ,')
        self._check_content(s3, t3, '(1 , 2 )')
        self._check_end_pos(tm, 3, 1)

    def test_attribute_spaces(self):
        s = 'func(x. y .z)'
        call = self._parse_value(s)
        self._check_content(s, call, s)
        self._check_content(s, call.args[0], 'x. y .z')

    def test_redundant_parenthesis(self):
        s = '( ( ( a + b ) ) )'
        v = ast.parse(s).body[0].value
        self.assertEqual(type(v).__name__, 'BinOp')
        self._check_content(s, v, 'a + b')
        s2 = 'await ' + s
        v = ast.parse(s2).body[0].value.value
        self.assertEqual(type(v).__name__, 'BinOp')
        self._check_content(s2, v, 'a + b')

    def test_trailers_with_redundant_parenthesis(self):
        tests = (
            ('( ( ( a ) ) ) ( )', 'Call'),
            ('( ( ( a ) ) ) ( b )', 'Call'),
            ('( ( ( a ) ) ) [ b ]', 'Subscript'),
            ('( ( ( a ) ) ) . b', 'Attribute'),
        )
        for s, t in tests:
            with self.subTest(s):
                v = ast.parse(s).body[0].value
                self.assertEqual(type(v).__name__, t)
                self._check_content(s, v, s)
                s2 = 'await ' + s
                v = ast.parse(s2).body[0].value.value
                self.assertEqual(type(v).__name__, t)
                self._check_content(s2, v, s)

    def test_displays(self):
        s1 = '[{}, {1, }, {1, 2,} ]'
        s2 = '{a: b, f (): g () ,}'
        c1 = self._parse_value(s1)
        c2 = self._parse_value(s2)
        self._check_content(s1, c1.elts[0], '{}')
        self._check_content(s1, c1.elts[1], '{1, }')
        self._check_content(s1, c1.elts[2], '{1, 2,}')
        self._check_content(s2, c2.keys[1], 'f ()')
        self._check_content(s2, c2.values[1], 'g ()')

    def test_comprehensions(self):
        s = dedent('''
            x = [{x for x, y in stuff
                  if cond.x} for stuff in things]
        ''').strip()
        cmp = self._parse_value(s)
        self._check_end_pos(cmp, 2, 37)
        self._check_content(s, cmp.generators[0].iter, 'things')
        self._check_content(s, cmp.elt.generators[0].iter, 'stuff')
        self._check_content(s, cmp.elt.generators[0].ifs[0], 'cond.x')
        self._check_content(s, cmp.elt.generators[0].target, 'x, y')

    def test_yield_await(self):
        s = dedent('''
            async def f():
                yield x
                await y
        ''').strip()
        fdef = ast.parse(s).body[0]
        self._check_content(s, fdef.body[0].value, 'yield x')
        self._check_content(s, fdef.body[1].value, 'await y')

    def test_source_segment_multi(self):
        s_orig = dedent('''
            x = (
                a, b,
            ) + ()
        ''').strip()
        s_tuple = dedent('''
            (
                a, b,
            )
        ''').strip()
        binop = self._parse_value(s_orig)
        self.assertEqual(ast.get_source_segment(s_orig, binop.left), s_tuple)

    def test_source_segment_padded(self):
        s_orig = dedent('''
            class C:
                def fun(self) -> None:
                    "ЖЖЖЖЖ"
        ''').strip()
        s_method = '    def fun(self) -> None:\n' \
                   '        "ЖЖЖЖЖ"'
        cdef = ast.parse(s_orig).body[0]
        self.assertEqual(ast.get_source_segment(s_orig, cdef.body[0], padded=True),
                         s_method)

    def test_source_segment_endings(self):
        s = 'v = 1\r\nw = 1\nx = 1\n\ry = 1\rz = 1\r\n'
        v, w, x, y, z = ast.parse(s).body
        self._check_content(s, v, 'v = 1')
        self._check_content(s, w, 'w = 1')
        self._check_content(s, x, 'x = 1')
        self._check_content(s, y, 'y = 1')
        self._check_content(s, z, 'z = 1')

    def test_source_segment_tabs(self):
        s = dedent('''
            class C:
              \t\f  def fun(self) -> None:
              \t\f      pass
        ''').strip()
        s_method = '  \t\f  def fun(self) -> None:\n' \
                   '  \t\f      pass'

        cdef = ast.parse(s).body[0]
        self.assertEqual(ast.get_source_segment(s, cdef.body[0], padded=True), s_method)

    def test_source_segment_newlines(self):
        s = 'def f():\n  pass\ndef g():\r  pass\r\ndef h():\r\n  pass\r\n'
        f, g, h = ast.parse(s).body
        self._check_content(s, f, 'def f():\n  pass')
        self._check_content(s, g, 'def g():\r  pass')
        self._check_content(s, h, 'def h():\r\n  pass')

        s = 'def f():\n  a = 1\r  b = 2\r\n  c = 3\n'
        f = ast.parse(s).body[0]
        self._check_content(s, f, s.rstrip())

    def test_source_segment_missing_info(self):
        s = 'v = 1\r\nw = 1\nx = 1\n\ry = 1\r\n'
        v, w, x, y = ast.parse(s).body
        del v.lineno
        del w.end_lineno
        del x.col_offset
        del y.end_col_offset
        self.assertIsNone(ast.get_source_segment(s, v))
        self.assertIsNone(ast.get_source_segment(s, w))
        self.assertIsNone(ast.get_source_segment(s, x))
        self.assertIsNone(ast.get_source_segment(s, y))


class NodeTransformerTests(ASTTestMixin, unittest.TestCase):
    def assertASTTransformation(self, tranformer_class,
                                initial_code, expected_code):
        initial_ast = ast.parse(dedent(initial_code))
        expected_ast = ast.parse(dedent(expected_code))

        tranformer = tranformer_class()
        result_ast = ast.fix_missing_locations(tranformer.visit(initial_ast))

        self.assertASTEqual(result_ast, expected_ast)

    def test_node_remove_single(self):
        code = 'def func(arg) -> SomeType: ...'
        expected = 'def func(arg): ...'

        # Since `FunctionDef.returns` is defined as a single value, we test
        # the `if isinstance(old_value, AST):` branch here.
        class SomeTypeRemover(ast.NodeTransformer):
            def visit_Name(self, node: ast.Name):
                self.generic_visit(node)
                if node.id == 'SomeType':
                    return None
                return node

        self.assertASTTransformation(SomeTypeRemover, code, expected)

    def test_node_remove_from_list(self):
        code = """
        def func(arg):
            print(arg)
            yield arg
        """
        expected = """
        def func(arg):
            print(arg)
        """

        # Since `FunctionDef.body` is defined as a list, we test
        # the `if isinstance(old_value, list):` branch here.
        class YieldRemover(ast.NodeTransformer):
            def visit_Expr(self, node: ast.Expr):
                self.generic_visit(node)
                if isinstance(node.value, ast.Yield):
                    return None  # Remove `yield` from a function
                return node

        self.assertASTTransformation(YieldRemover, code, expected)

    def test_node_return_list(self):
        code = """
        class DSL(Base, kw1=True): ...
        """
        expected = """
        class DSL(Base, kw1=True, kw2=True, kw3=False): ...
        """

        class ExtendKeywords(ast.NodeTransformer):
            def visit_keyword(self, node: ast.keyword):
                self.generic_visit(node)
                if node.arg == 'kw1':
                    return [
                        node,
                        ast.keyword('kw2', ast.Constant(True)),
                        ast.keyword('kw3', ast.Constant(False)),
                    ]
                return node

        self.assertASTTransformation(ExtendKeywords, code, expected)

    def test_node_mutate(self):
        code = """
        def func(arg):
            print(arg)
        """
        expected = """
        def func(arg):
            log(arg)
        """

        class PrintToLog(ast.NodeTransformer):
            def visit_Call(self, node: ast.Call):
                self.generic_visit(node)
                if isinstance(node.func, ast.Name) and node.func.id == 'print':
                    node.func.id = 'log'
                return node

        self.assertASTTransformation(PrintToLog, code, expected)

    def test_node_replace(self):
        code = """
        def func(arg):
            print(arg)
        """
        expected = """
        def func(arg):
            logger.log(arg, debug=True)
        """

        class PrintToLog(ast.NodeTransformer):
            def visit_Call(self, node: ast.Call):
                self.generic_visit(node)
                if isinstance(node.func, ast.Name) and node.func.id == 'print':
                    return ast.Call(
                        func=ast.Attribute(
                            ast.Name('logger', ctx=ast.Load()),
                            attr='log',
                            ctx=ast.Load(),
                        ),
                        args=node.args,
                        keywords=[ast.keyword('debug', ast.Constant(True))],
                    )
                return node

        self.assertASTTransformation(PrintToLog, code, expected)


class ASTConstructorTests(unittest.TestCase):
    """Test the autogenerated constructors for AST nodes."""

    def test_FunctionDef(self):
        args = ast.arguments()
        self.assertEqual(args.args, [])
        self.assertEqual(args.posonlyargs, [])
        with self.assertWarnsRegex(DeprecationWarning,
                                   r"FunctionDef\.__init__ missing 1 required positional argument: 'name'"):
            node = ast.FunctionDef(args=args)
        self.assertFalse(hasattr(node, "name"))
        self.assertEqual(node.decorator_list, [])
        node = ast.FunctionDef(name='foo', args=args)
        self.assertEqual(node.name, 'foo')
        self.assertEqual(node.decorator_list, [])

    def test_expr_context(self):
        name = ast.Name("x")
        self.assertEqual(name.id, "x")
        self.assertIsInstance(name.ctx, ast.Load)

        name2 = ast.Name("x", ast.Store())
        self.assertEqual(name2.id, "x")
        self.assertIsInstance(name2.ctx, ast.Store)

        name3 = ast.Name("x", ctx=ast.Del())
        self.assertEqual(name3.id, "x")
        self.assertIsInstance(name3.ctx, ast.Del)

        with self.assertWarnsRegex(DeprecationWarning,
                                   r"Name\.__init__ missing 1 required positional argument: 'id'"):
            name3 = ast.Name()

    def test_custom_subclass_with_no_fields(self):
        class NoInit(ast.AST):
            pass

        obj = NoInit()
        self.assertIsInstance(obj, NoInit)
        self.assertEqual(obj.__dict__, {})

    def test_fields_but_no_field_types(self):
        class Fields(ast.AST):
            _fields = ('a',)

        obj = Fields()
        with self.assertRaises(AttributeError):
            obj.a
        obj = Fields(a=1)
        self.assertEqual(obj.a, 1)

    def test_fields_and_types(self):
        class FieldsAndTypes(ast.AST):
            _fields = ('a',)
            _field_types = {'a': int | None}
            a: int | None = None

        obj = FieldsAndTypes()
        self.assertIs(obj.a, None)
        obj = FieldsAndTypes(a=1)
        self.assertEqual(obj.a, 1)

    def test_fields_and_types_no_default(self):
        class FieldsAndTypesNoDefault(ast.AST):
            _fields = ('a',)
            _field_types = {'a': int}

        with self.assertWarnsRegex(DeprecationWarning,
                                   r"FieldsAndTypesNoDefault\.__init__ missing 1 required positional argument: 'a'\."):
            obj = FieldsAndTypesNoDefault()
        with self.assertRaises(AttributeError):
            obj.a
        obj = FieldsAndTypesNoDefault(a=1)
        self.assertEqual(obj.a, 1)

    def test_incomplete_field_types(self):
        class MoreFieldsThanTypes(ast.AST):
            _fields = ('a', 'b')
            _field_types = {'a': int | None}
            a: int | None = None
            b: int | None = None

        with self.assertWarnsRegex(
            DeprecationWarning,
            r"Field 'b' is missing from MoreFieldsThanTypes\._field_types"
        ):
            obj = MoreFieldsThanTypes()
        self.assertIs(obj.a, None)
        self.assertIs(obj.b, None)

        obj = MoreFieldsThanTypes(a=1, b=2)
        self.assertEqual(obj.a, 1)
        self.assertEqual(obj.b, 2)

    def test_complete_field_types(self):
        class _AllFieldTypes(ast.AST):
            _fields = ('a', 'b')
            _field_types = {'a': int | None, 'b': list[str]}
            # This must be set explicitly
            a: int | None = None
            # This will add an implicit empty list default
            b: list[str]

        obj = _AllFieldTypes()
        self.assertIs(obj.a, None)
        self.assertEqual(obj.b, [])


@support.cpython_only
class ModuleStateTests(unittest.TestCase):
    # bpo-41194, bpo-41261, bpo-41631: The _ast module uses a global state.

    def check_ast_module(self):
        # Check that the _ast module still works as expected
        code = 'x + 1'
        filename = '<string>'
        mode = 'eval'

        # Create _ast.AST subclasses instances
        ast_tree = compile(code, filename, mode, flags=ast.PyCF_ONLY_AST)

        # Call PyAST_Check()
        code = compile(ast_tree, filename, mode)
        self.assertIsInstance(code, types.CodeType)

    def test_reload_module(self):
        # bpo-41194: Importing the _ast module twice must not crash.
        with support.swap_item(sys.modules, '_ast', None):
            del sys.modules['_ast']
            import _ast as ast1

            del sys.modules['_ast']
            import _ast as ast2

            self.check_ast_module()

        # Unloading the two _ast module instances must not crash.
        del ast1
        del ast2
        support.gc_collect()

        self.check_ast_module()

    def test_sys_modules(self):
        # bpo-41631: Test reproducing a Mercurial crash when PyAST_Check()
        # imported the _ast module internally.
        lazy_mod = object()

        def my_import(name, *args, **kw):
            sys.modules[name] = lazy_mod
            return lazy_mod

        with support.swap_item(sys.modules, '_ast', None):
            del sys.modules['_ast']

            with support.swap_attr(builtins, '__import__', my_import):
                # Test that compile() does not import the _ast module
                self.check_ast_module()
                self.assertNotIn('_ast', sys.modules)

                # Sanity check of the test itself
                import _ast
                self.assertIs(_ast, lazy_mod)

    def test_subinterpreter(self):
        # bpo-41631: Importing and using the _ast module in a subinterpreter
        # must not crash.
        code = dedent('''
            import _ast
            import ast
            import gc
            import sys
            import types

            # Create _ast.AST subclasses instances and call PyAST_Check()
            ast_tree = compile('x+1', '<string>', 'eval',
                               flags=ast.PyCF_ONLY_AST)
            code = compile(ast_tree, 'string', 'eval')
            if not isinstance(code, types.CodeType):
                raise AssertionError

            # Unloading the _ast module must not crash.
            del ast, _ast
            del sys.modules['ast'], sys.modules['_ast']
            gc.collect()
        ''')
        res = support.run_in_subinterp(code)
        self.assertEqual(res, 0)


class ASTMainTests(unittest.TestCase):
    # Tests `ast.main()` function.

    def test_cli_file_input(self):
        code = "print(1, 2, 3)"
        expected = ast.dump(ast.parse(code), indent=3)

        with os_helper.temp_dir() as tmp_dir:
            filename = os.path.join(tmp_dir, "test_module.py")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(code)
            res, _ = script_helper.run_python_until_end("-m", "ast", filename)

        self.assertEqual(res.err, b"")
        self.assertEqual(expected.splitlines(),
                         res.out.decode("utf8").splitlines())
        self.assertEqual(res.rc, 0)


def main():
    if __name__ != '__main__':
        return
    if sys.argv[1:] == ['-g']:
        for statements, kind in ((exec_tests, "exec"), (single_tests, "single"),
                                 (eval_tests, "eval")):
            print(kind+"_results = [")
            for statement in statements:
                tree = ast.parse(statement, "?", kind)
                print("%r," % (to_tuple(tree),))
            print("]")
        print("main()")
        raise SystemExit
    unittest.main()

#### EVERYTHING BELOW IS GENERATED BY python Lib/test/test_ast.py -g  #####
exec_results = [
('Module', [('Expr', (1, 0, 1, 18), ('Constant', (1, 0, 1, 18), 'module docstring', None))], []),
('Module', [('FunctionDef', (1, 0, 1, 13), 'f', ('arguments', [], [], None, [], [], None, []), [('Pass', (1, 9, 1, 13))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 29), 'f', ('arguments', [], [], None, [], [], None, []), [('Expr', (1, 9, 1, 29), ('Constant', (1, 9, 1, 29), 'function docstring', None))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 14), 'f', ('arguments', [], [('arg', (1, 6, 1, 7), 'a', None, None)], None, [], [], None, []), [('Pass', (1, 10, 1, 14))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 16), 'f', ('arguments', [], [('arg', (1, 6, 1, 7), 'a', None, None)], None, [], [], None, [('Constant', (1, 8, 1, 9), 0, None)]), [('Pass', (1, 12, 1, 16))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 18), 'f', ('arguments', [], [], ('arg', (1, 7, 1, 11), 'args', None, None), [], [], None, []), [('Pass', (1, 14, 1, 18))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 23), 'f', ('arguments', [], [], ('arg', (1, 7, 1, 16), 'args', ('Starred', (1, 13, 1, 16), ('Name', (1, 14, 1, 16), 'Ts', ('Load',)), ('Load',)), None), [], [], None, []), [('Pass', (1, 19, 1, 23))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 36), 'f', ('arguments', [], [], ('arg', (1, 7, 1, 29), 'args', ('Starred', (1, 13, 1, 29), ('Subscript', (1, 14, 1, 29), ('Name', (1, 14, 1, 19), 'tuple', ('Load',)), ('Tuple', (1, 20, 1, 28), [('Name', (1, 20, 1, 23), 'int', ('Load',)), ('Constant', (1, 25, 1, 28), Ellipsis, None)], ('Load',)), ('Load',)), ('Load',)), None), [], [], None, []), [('Pass', (1, 32, 1, 36))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 36), 'f', ('arguments', [], [], ('arg', (1, 7, 1, 29), 'args', ('Starred', (1, 13, 1, 29), ('Subscript', (1, 14, 1, 29), ('Name', (1, 14, 1, 19), 'tuple', ('Load',)), ('Tuple', (1, 20, 1, 28), [('Name', (1, 20, 1, 23), 'int', ('Load',)), ('Starred', (1, 25, 1, 28), ('Name', (1, 26, 1, 28), 'Ts', ('Load',)), ('Load',))], ('Load',)), ('Load',)), ('Load',)), None), [], [], None, []), [('Pass', (1, 32, 1, 36))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 21), 'f', ('arguments', [], [], None, [], [], ('arg', (1, 8, 1, 14), 'kwargs', None, None), []), [('Pass', (1, 17, 1, 21))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 71), 'f', ('arguments', [], [('arg', (1, 6, 1, 7), 'a', None, None), ('arg', (1, 9, 1, 10), 'b', None, None), ('arg', (1, 14, 1, 15), 'c', None, None), ('arg', (1, 22, 1, 23), 'd', None, None), ('arg', (1, 28, 1, 29), 'e', None, None)], ('arg', (1, 35, 1, 39), 'args', None, None), [('arg', (1, 41, 1, 42), 'f', None, None)], [('Constant', (1, 43, 1, 45), 42, None)], ('arg', (1, 49, 1, 55), 'kwargs', None, None), [('Constant', (1, 11, 1, 12), 1, None), ('Constant', (1, 16, 1, 20), None, None), ('List', (1, 24, 1, 26), [], ('Load',)), ('Dict', (1, 30, 1, 32), [], [])]), [('Expr', (1, 58, 1, 71), ('Constant', (1, 58, 1, 71), 'doc for f()', None))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 27), 'f', ('arguments', [], [], None, [], [], None, []), [('Pass', (1, 23, 1, 27))], [], ('Subscript', (1, 11, 1, 21), ('Name', (1, 11, 1, 16), 'tuple', ('Load',)), ('Tuple', (1, 17, 1, 20), [('Starred', (1, 17, 1, 20), ('Name', (1, 18, 1, 20), 'Ts', ('Load',)), ('Load',))], ('Load',)), ('Load',)), None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 32), 'f', ('arguments', [], [], None, [], [], None, []), [('Pass', (1, 28, 1, 32))], [], ('Subscript', (1, 11, 1, 26), ('Name', (1, 11, 1, 16), 'tuple', ('Load',)), ('Tuple', (1, 17, 1, 25), [('Name', (1, 17, 1, 20), 'int', ('Load',)), ('Starred', (1, 22, 1, 25), ('Name', (1, 23, 1, 25), 'Ts', ('Load',)), ('Load',))], ('Load',)), ('Load',)), None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 45), 'f', ('arguments', [], [], None, [], [], None, []), [('Pass', (1, 41, 1, 45))], [], ('Subscript', (1, 11, 1, 39), ('Name', (1, 11, 1, 16), 'tuple', ('Load',)), ('Tuple', (1, 17, 1, 38), [('Name', (1, 17, 1, 20), 'int', ('Load',)), ('Starred', (1, 22, 1, 38), ('Subscript', (1, 23, 1, 38), ('Name', (1, 23, 1, 28), 'tuple', ('Load',)), ('Tuple', (1, 29, 1, 37), [('Name', (1, 29, 1, 32), 'int', ('Load',)), ('Constant', (1, 34, 1, 37), Ellipsis, None)], ('Load',)), ('Load',)), ('Load',))], ('Load',)), ('Load',)), None, [])], []),
('Module', [('ClassDef', (1, 0, 1, 12), 'C', [], [], [('Pass', (1, 8, 1, 12))], [], [])], []),
('Module', [('ClassDef', (1, 0, 1, 32), 'C', [], [], [('Expr', (1, 9, 1, 32), ('Constant', (1, 9, 1, 32), 'docstring for class C', None))], [], [])], []),
('Module', [('ClassDef', (1, 0, 1, 21), 'C', [('Name', (1, 8, 1, 14), 'object', ('Load',))], [], [('Pass', (1, 17, 1, 21))], [], [])], []),
('Module', [('ClassDef', (1, 0, 1, 19), 'C', [('Name', (1, 8, 1, 9), 'A', ('Load',)), ('Name', (1, 11, 1, 12), 'B', ('Load',))], [], [('Pass', (1, 15, 1, 19))], [], [])], []),
('Module', [('FunctionDef', (1, 0, 1, 16), 'f', ('arguments', [], [], None, [], [], None, []), [('Return', (1, 8, 1, 16), ('Constant', (1, 15, 1, 16), 1, None))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 14), 'f', ('arguments', [], [], None, [], [], None, []), [('Return', (1, 8, 1, 14), None)], [], None, None, [])], []),
('Module', [('Delete', (1, 0, 1, 5), [('Name', (1, 4, 1, 5), 'v', ('Del',))])], []),
('Module', [('Assign', (1, 0, 1, 5), [('Name', (1, 0, 1, 1), 'v', ('Store',))], ('Constant', (1, 4, 1, 5), 1, None), None)], []),
('Module', [('Assign', (1, 0, 1, 7), [('Tuple', (1, 0, 1, 3), [('Name', (1, 0, 1, 1), 'a', ('Store',)), ('Name', (1, 2, 1, 3), 'b', ('Store',))], ('Store',))], ('Name', (1, 6, 1, 7), 'c', ('Load',)), None)], []),
('Module', [('Assign', (1, 0, 1, 9), [('Tuple', (1, 0, 1, 5), [('Name', (1, 1, 1, 2), 'a', ('Store',)), ('Name', (1, 3, 1, 4), 'b', ('Store',))], ('Store',))], ('Name', (1, 8, 1, 9), 'c', ('Load',)), None)], []),
('Module', [('Assign', (1, 0, 1, 9), [('List', (1, 0, 1, 5), [('Name', (1, 1, 1, 2), 'a', ('Store',)), ('Name', (1, 3, 1, 4), 'b', ('Store',))], ('Store',))], ('Name', (1, 8, 1, 9), 'c', ('Load',)), None)], []),
('Module', [('Assign', (1, 0, 1, 8), [('Subscript', (1, 0, 1, 4), ('Name', (1, 0, 1, 1), 'a', ('Load',)), ('Name', (1, 2, 1, 3), 'b', ('Load',)), ('Store',))], ('Name', (1, 7, 1, 8), 'c', ('Load',)), None)], []),
('Module', [('AnnAssign', (1, 0, 1, 13), ('Name', (1, 0, 1, 1), 'x', ('Store',)), ('Subscript', (1, 3, 1, 13), ('Name', (1, 3, 1, 8), 'tuple', ('Load',)), ('Tuple', (1, 9, 1, 12), [('Starred', (1, 9, 1, 12), ('Name', (1, 10, 1, 12), 'Ts', ('Load',)), ('Load',))], ('Load',)), ('Load',)), None, 1)], []),
('Module', [('AnnAssign', (1, 0, 1, 18), ('Name', (1, 0, 1, 1), 'x', ('Store',)), ('Subscript', (1, 3, 1, 18), ('Name', (1, 3, 1, 8), 'tuple', ('Load',)), ('Tuple', (1, 9, 1, 17), [('Name', (1, 9, 1, 12), 'int', ('Load',)), ('Starred', (1, 14, 1, 17), ('Name', (1, 15, 1, 17), 'Ts', ('Load',)), ('Load',))], ('Load',)), ('Load',)), None, 1)], []),
('Module', [('AnnAssign', (1, 0, 1, 31), ('Name', (1, 0, 1, 1), 'x', ('Store',)), ('Subscript', (1, 3, 1, 31), ('Name', (1, 3, 1, 8), 'tuple', ('Load',)), ('Tuple', (1, 9, 1, 30), [('Name', (1, 9, 1, 12), 'int', ('Load',)), ('Starred', (1, 14, 1, 30), ('Subscript', (1, 15, 1, 30), ('Name', (1, 15, 1, 20), 'tuple', ('Load',)), ('Tuple', (1, 21, 1, 29), [('Name', (1, 21, 1, 24), 'str', ('Load',)), ('Constant', (1, 26, 1, 29), Ellipsis, None)], ('Load',)), ('Load',)), ('Load',))], ('Load',)), ('Load',)), None, 1)], []),
('Module', [('AugAssign', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'v', ('Store',)), ('Add',), ('Constant', (1, 5, 1, 6), 1, None))], []),
('Module', [('AugAssign', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'v', ('Store',)), ('Sub',), ('Constant', (1, 5, 1, 6), 1, None))], []),
('Module', [('AugAssign', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'v', ('Store',)), ('Mult',), ('Constant', (1, 5, 1, 6), 1, None))], []),
('Module', [('AugAssign', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'v', ('Store',)), ('MatMult',), ('Constant', (1, 5, 1, 6), 1, None))], []),
('Module', [('AugAssign', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'v', ('Store',)), ('Div',), ('Constant', (1, 5, 1, 6), 1, None))], []),
('Module', [('AugAssign', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'v', ('Store',)), ('Mod',), ('Constant', (1, 5, 1, 6), 1, None))], []),
('Module', [('AugAssign', (1, 0, 1, 7), ('Name', (1, 0, 1, 1), 'v', ('Store',)), ('Pow',), ('Constant', (1, 6, 1, 7), 1, None))], []),
('Module', [('AugAssign', (1, 0, 1, 7), ('Name', (1, 0, 1, 1), 'v', ('Store',)), ('LShift',), ('Constant', (1, 6, 1, 7), 1, None))], []),
('Module', [('AugAssign', (1, 0, 1, 7), ('Name', (1, 0, 1, 1), 'v', ('Store',)), ('RShift',), ('Constant', (1, 6, 1, 7), 1, None))], []),
('Module', [('AugAssign', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'v', ('Store',)), ('BitOr',), ('Constant', (1, 5, 1, 6), 1, None))], []),
('Module', [('AugAssign', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'v', ('Store',)), ('BitXor',), ('Constant', (1, 5, 1, 6), 1, None))], []),
('Module', [('AugAssign', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'v', ('Store',)), ('BitAnd',), ('Constant', (1, 5, 1, 6), 1, None))], []),
('Module', [('AugAssign', (1, 0, 1, 7), ('Name', (1, 0, 1, 1), 'v', ('Store',)), ('FloorDiv',), ('Constant', (1, 6, 1, 7), 1, None))], []),
('Module', [('For', (1, 0, 1, 15), ('Name', (1, 4, 1, 5), 'v', ('Store',)), ('Name', (1, 9, 1, 10), 'v', ('Load',)), [('Pass', (1, 11, 1, 15))], [], None)], []),
('Module', [('For', (1, 0, 4, 6), ('Name', (1, 4, 1, 5), 'v', ('Store',)), ('Name', (1, 9, 1, 10), 'v', ('Load',)), [('Pass', (2, 2, 2, 6))], [('Pass', (4, 2, 4, 6))], None)], []),
('Module', [('While', (1, 0, 1, 12), ('Name', (1, 6, 1, 7), 'v', ('Load',)), [('Pass', (1, 8, 1, 12))], [])], []),
('Module', [('While', (1, 0, 4, 6), ('Name', (1, 6, 1, 7), 'v', ('Load',)), [('Pass', (2, 2, 2, 6))], [('Pass', (4, 2, 4, 6))])], []),
('Module', [('If', (1, 0, 1, 9), ('Name', (1, 3, 1, 4), 'v', ('Load',)), [('Pass', (1, 5, 1, 9))], [])], []),
('Module', [('If', (1, 0, 4, 6), ('Name', (1, 3, 1, 4), 'a', ('Load',)), [('Pass', (2, 2, 2, 6))], [('If', (3, 0, 4, 6), ('Name', (3, 5, 3, 6), 'b', ('Load',)), [('Pass', (4, 2, 4, 6))], [])])], []),
('Module', [('If', (1, 0, 4, 6), ('Name', (1, 3, 1, 4), 'a', ('Load',)), [('Pass', (2, 2, 2, 6))], [('Pass', (4, 2, 4, 6))])], []),
('Module', [('If', (1, 0, 6, 6), ('Name', (1, 3, 1, 4), 'a', ('Load',)), [('Pass', (2, 2, 2, 6))], [('If', (3, 0, 6, 6), ('Name', (3, 5, 3, 6), 'b', ('Load',)), [('Pass', (4, 2, 4, 6))], [('Pass', (6, 2, 6, 6))])])], []),
('Module', [('If', (1, 0, 10, 6), ('Name', (1, 3, 1, 4), 'a', ('Load',)), [('Pass', (2, 2, 2, 6))], [('If', (3, 0, 10, 6), ('Name', (3, 5, 3, 6), 'b', ('Load',)), [('Pass', (4, 2, 4, 6))], [('If', (5, 0, 10, 6), ('Name', (5, 5, 5, 6), 'b', ('Load',)), [('Pass', (6, 2, 6, 6))], [('If', (7, 0, 10, 6), ('Name', (7, 5, 7, 6), 'b', ('Load',)), [('Pass', (8, 2, 8, 6))], [('Pass', (10, 2, 10, 6))])])])])], []),
('Module', [('With', (1, 0, 1, 12), [('withitem', ('Name', (1, 5, 1, 6), 'x', ('Load',)), None)], [('Pass', (1, 8, 1, 12))], None)], []),
('Module', [('With', (1, 0, 1, 15), [('withitem', ('Name', (1, 5, 1, 6), 'x', ('Load',)), None), ('withitem', ('Name', (1, 8, 1, 9), 'y', ('Load',)), None)], [('Pass', (1, 11, 1, 15))], None)], []),
('Module', [('With', (1, 0, 1, 17), [('withitem', ('Name', (1, 5, 1, 6), 'x', ('Load',)), ('Name', (1, 10, 1, 11), 'y', ('Store',)))], [('Pass', (1, 13, 1, 17))], None)], []),
('Module', [('With', (1, 0, 1, 25), [('withitem', ('Name', (1, 5, 1, 6), 'x', ('Load',)), ('Name', (1, 10, 1, 11), 'y', ('Store',))), ('withitem', ('Name', (1, 13, 1, 14), 'z', ('Load',)), ('Name', (1, 18, 1, 19), 'q', ('Store',)))], [('Pass', (1, 21, 1, 25))], None)], []),
('Module', [('With', (1, 0, 1, 19), [('withitem', ('Name', (1, 6, 1, 7), 'x', ('Load',)), ('Name', (1, 11, 1, 12), 'y', ('Store',)))], [('Pass', (1, 15, 1, 19))], None)], []),
('Module', [('With', (1, 0, 1, 17), [('withitem', ('Name', (1, 6, 1, 7), 'x', ('Load',)), None), ('withitem', ('Name', (1, 9, 1, 10), 'y', ('Load',)), None)], [('Pass', (1, 13, 1, 17))], None)], []),
('Module', [('Raise', (1, 0, 1, 5), None, None)], []),
('Module', [('Raise', (1, 0, 1, 25), ('Call', (1, 6, 1, 25), ('Name', (1, 6, 1, 15), 'Exception', ('Load',)), [('Constant', (1, 16, 1, 24), 'string', None)], []), None)], []),
('Module', [('Raise', (1, 0, 1, 15), ('Name', (1, 6, 1, 15), 'Exception', ('Load',)), None)], []),
('Module', [('Raise', (1, 0, 1, 35), ('Call', (1, 6, 1, 25), ('Name', (1, 6, 1, 15), 'Exception', ('Load',)), [('Constant', (1, 16, 1, 24), 'string', None)], []), ('Constant', (1, 31, 1, 35), None, None))], []),
('Module', [('Try', (1, 0, 4, 6), [('Pass', (2, 2, 2, 6))], [('ExceptHandler', (3, 0, 4, 6), ('Name', (3, 7, 3, 16), 'Exception', ('Load',)), None, [('Pass', (4, 2, 4, 6))])], [], [])], []),
('Module', [('Try', (1, 0, 4, 6), [('Pass', (2, 2, 2, 6))], [('ExceptHandler', (3, 0, 4, 6), ('Name', (3, 7, 3, 16), 'Exception', ('Load',)), 'exc', [('Pass', (4, 2, 4, 6))])], [], [])], []),
('Module', [('Try', (1, 0, 4, 6), [('Pass', (2, 2, 2, 6))], [], [], [('Pass', (4, 2, 4, 6))])], []),
('Module', [('TryStar', (1, 0, 4, 6), [('Pass', (2, 2, 2, 6))], [('ExceptHandler', (3, 0, 4, 6), ('Name', (3, 8, 3, 17), 'Exception', ('Load',)), None, [('Pass', (4, 2, 4, 6))])], [], [])], []),
('Module', [('TryStar', (1, 0, 4, 6), [('Pass', (2, 2, 2, 6))], [('ExceptHandler', (3, 0, 4, 6), ('Name', (3, 8, 3, 17), 'Exception', ('Load',)), 'exc', [('Pass', (4, 2, 4, 6))])], [], [])], []),
('Module', [('Try', (1, 0, 7, 6), [('Pass', (2, 2, 2, 6))], [('ExceptHandler', (3, 0, 4, 6), ('Name', (3, 7, 3, 16), 'Exception', ('Load',)), None, [('Pass', (4, 2, 4, 6))])], [('Pass', (5, 7, 5, 11))], [('Pass', (7, 2, 7, 6))])], []),
('Module', [('Try', (1, 0, 7, 6), [('Pass', (2, 2, 2, 6))], [('ExceptHandler', (3, 0, 4, 6), ('Name', (3, 7, 3, 16), 'Exception', ('Load',)), 'exc', [('Pass', (4, 2, 4, 6))])], [('Pass', (5, 7, 5, 11))], [('Pass', (7, 2, 7, 6))])], []),
('Module', [('TryStar', (1, 0, 7, 6), [('Pass', (2, 2, 2, 6))], [('ExceptHandler', (3, 0, 4, 6), ('Name', (3, 8, 3, 17), 'Exception', ('Load',)), 'exc', [('Pass', (4, 2, 4, 6))])], [('Pass', (5, 7, 5, 11))], [('Pass', (7, 2, 7, 6))])], []),
('Module', [('Assert', (1, 0, 1, 8), ('Name', (1, 7, 1, 8), 'v', ('Load',)), None)], []),
('Module', [('Assert', (1, 0, 1, 19), ('Name', (1, 7, 1, 8), 'v', ('Load',)), ('Constant', (1, 10, 1, 19), 'message', None))], []),
('Module', [('Import', (1, 0, 1, 10), [('alias', (1, 7, 1, 10), 'sys', None)])], []),
('Module', [('Import', (1, 0, 1, 17), [('alias', (1, 7, 1, 17), 'foo', 'bar')])], []),
('Module', [('ImportFrom', (1, 0, 1, 22), 'sys', [('alias', (1, 16, 1, 22), 'x', 'y')], 0)], []),
('Module', [('ImportFrom', (1, 0, 1, 17), 'sys', [('alias', (1, 16, 1, 17), 'v', None)], 0)], []),
('Module', [('Global', (1, 0, 1, 8), ['v'])], []),
('Module', [('Expr', (1, 0, 1, 1), ('Constant', (1, 0, 1, 1), 1, None))], []),
('Module', [('Pass', (1, 0, 1, 4))], []),
('Module', [('For', (1, 0, 1, 16), ('Name', (1, 4, 1, 5), 'v', ('Store',)), ('Name', (1, 9, 1, 10), 'v', ('Load',)), [('Break', (1, 11, 1, 16))], [], None)], []),
('Module', [('For', (1, 0, 1, 19), ('Name', (1, 4, 1, 5), 'v', ('Store',)), ('Name', (1, 9, 1, 10), 'v', ('Load',)), [('Continue', (1, 11, 1, 19))], [], None)], []),
('Module', [('For', (1, 0, 1, 18), ('Tuple', (1, 4, 1, 7), [('Name', (1, 4, 1, 5), 'a', ('Store',)), ('Name', (1, 6, 1, 7), 'b', ('Store',))], ('Store',)), ('Name', (1, 11, 1, 12), 'c', ('Load',)), [('Pass', (1, 14, 1, 18))], [], None)], []),
('Module', [('For', (1, 0, 1, 20), ('Tuple', (1, 4, 1, 9), [('Name', (1, 5, 1, 6), 'a', ('Store',)), ('Name', (1, 7, 1, 8), 'b', ('Store',))], ('Store',)), ('Name', (1, 13, 1, 14), 'c', ('Load',)), [('Pass', (1, 16, 1, 20))], [], None)], []),
('Module', [('For', (1, 0, 1, 20), ('List', (1, 4, 1, 9), [('Name', (1, 5, 1, 6), 'a', ('Store',)), ('Name', (1, 7, 1, 8), 'b', ('Store',))], ('Store',)), ('Name', (1, 13, 1, 14), 'c', ('Load',)), [('Pass', (1, 16, 1, 20))], [], None)], []),
('Module', [('Expr', (1, 0, 11, 5), ('GeneratorExp', (1, 0, 11, 5), ('Tuple', (2, 4, 6, 5), [('Name', (3, 4, 3, 6), 'Aa', ('Load',)), ('Name', (5, 7, 5, 9), 'Bb', ('Load',))], ('Load',)), [('comprehension', ('Tuple', (8, 4, 10, 6), [('Name', (8, 4, 8, 6), 'Aa', ('Store',)), ('Name', (10, 4, 10, 6), 'Bb', ('Store',))], ('Store',)), ('Name', (10, 10, 10, 12), 'Cc', ('Load',)), [], 0)]))], []),
('Module', [('Expr', (1, 0, 1, 34), ('DictComp', (1, 0, 1, 34), ('Name', (1, 1, 1, 2), 'a', ('Load',)), ('Name', (1, 5, 1, 6), 'b', ('Load',)), [('comprehension', ('Name', (1, 11, 1, 12), 'w', ('Store',)), ('Name', (1, 16, 1, 17), 'x', ('Load',)), [], 0), ('comprehension', ('Name', (1, 22, 1, 23), 'm', ('Store',)), ('Name', (1, 27, 1, 28), 'p', ('Load',)), [('Name', (1, 32, 1, 33), 'g', ('Load',))], 0)]))], []),
('Module', [('Expr', (1, 0, 1, 20), ('DictComp', (1, 0, 1, 20), ('Name', (1, 1, 1, 2), 'a', ('Load',)), ('Name', (1, 5, 1, 6), 'b', ('Load',)), [('comprehension', ('Tuple', (1, 11, 1, 14), [('Name', (1, 11, 1, 12), 'v', ('Store',)), ('Name', (1, 13, 1, 14), 'w', ('Store',))], ('Store',)), ('Name', (1, 18, 1, 19), 'x', ('Load',)), [], 0)]))], []),
('Module', [('Expr', (1, 0, 1, 19), ('SetComp', (1, 0, 1, 19), ('Name', (1, 1, 1, 2), 'r', ('Load',)), [('comprehension', ('Name', (1, 7, 1, 8), 'l', ('Store',)), ('Name', (1, 12, 1, 13), 'x', ('Load',)), [('Name', (1, 17, 1, 18), 'g', ('Load',))], 0)]))], []),
('Module', [('Expr', (1, 0, 1, 16), ('SetComp', (1, 0, 1, 16), ('Name', (1, 1, 1, 2), 'r', ('Load',)), [('comprehension', ('Tuple', (1, 7, 1, 10), [('Name', (1, 7, 1, 8), 'l', ('Store',)), ('Name', (1, 9, 1, 10), 'm', ('Store',))], ('Store',)), ('Name', (1, 14, 1, 15), 'x', ('Load',)), [], 0)]))], []),
('Module', [('AsyncFunctionDef', (1, 0, 3, 18), 'f', ('arguments', [], [], None, [], [], None, []), [('Expr', (2, 1, 2, 17), ('Constant', (2, 1, 2, 17), 'async function', None)), ('Expr', (3, 1, 3, 18), ('Await', (3, 1, 3, 18), ('Call', (3, 7, 3, 18), ('Name', (3, 7, 3, 16), 'something', ('Load',)), [], [])))], [], None, None, [])], []),
('Module', [('AsyncFunctionDef', (1, 0, 3, 8), 'f', ('arguments', [], [], None, [], [], None, []), [('AsyncFor', (2, 1, 3, 8), ('Name', (2, 11, 2, 12), 'e', ('Store',)), ('Name', (2, 16, 2, 17), 'i', ('Load',)), [('Expr', (2, 19, 2, 20), ('Constant', (2, 19, 2, 20), 1, None))], [('Expr', (3, 7, 3, 8), ('Constant', (3, 7, 3, 8), 2, None))], None)], [], None, None, [])], []),
('Module', [('AsyncFunctionDef', (1, 0, 2, 21), 'f', ('arguments', [], [], None, [], [], None, []), [('AsyncWith', (2, 1, 2, 21), [('withitem', ('Name', (2, 12, 2, 13), 'a', ('Load',)), ('Name', (2, 17, 2, 18), 'b', ('Store',)))], [('Expr', (2, 20, 2, 21), ('Constant', (2, 20, 2, 21), 1, None))], None)], [], None, None, [])], []),
('Module', [('Expr', (1, 0, 1, 14), ('Dict', (1, 0, 1, 14), [None, ('Constant', (1, 10, 1, 11), 2, None)], [('Dict', (1, 3, 1, 8), [('Constant', (1, 4, 1, 5), 1, None)], [('Constant', (1, 6, 1, 7), 2, None)]), ('Constant', (1, 12, 1, 13), 3, None)]))], []),
('Module', [('Expr', (1, 0, 1, 12), ('Set', (1, 0, 1, 12), [('Starred', (1, 1, 1, 8), ('Set', (1, 2, 1, 8), [('Constant', (1, 3, 1, 4), 1, None), ('Constant', (1, 6, 1, 7), 2, None)]), ('Load',)), ('Constant', (1, 10, 1, 11), 3, None)]))], []),
('Module', [('FunctionDef', (1, 0, 1, 16), 'f', ('arguments', [], [], None, [], [], None, []), [('Expr', (1, 9, 1, 16), ('Yield', (1, 9, 1, 16), ('Constant', (1, 15, 1, 16), 1, None)))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 22), 'f', ('arguments', [], [], None, [], [], None, []), [('Expr', (1, 9, 1, 22), ('YieldFrom', (1, 9, 1, 22), ('List', (1, 20, 1, 22), [], ('Load',))))], [], None, None, [])], []),
('Module', [('AsyncFunctionDef', (1, 0, 2, 21), 'f', ('arguments', [], [], None, [], [], None, []), [('Expr', (2, 1, 2, 21), ('ListComp', (2, 1, 2, 21), ('Name', (2, 2, 2, 3), 'i', ('Load',)), [('comprehension', ('Name', (2, 14, 2, 15), 'b', ('Store',)), ('Name', (2, 19, 2, 20), 'c', ('Load',)), [], 1)]))], [], None, None, [])], []),
('Module', [('FunctionDef', (4, 0, 4, 13), 'f', ('arguments', [], [], None, [], [], None, []), [('Pass', (4, 9, 4, 13))], [('Name', (1, 1, 1, 6), 'deco1', ('Load',)), ('Call', (2, 1, 2, 8), ('Name', (2, 1, 2, 6), 'deco2', ('Load',)), [], []), ('Call', (3, 1, 3, 9), ('Name', (3, 1, 3, 6), 'deco3', ('Load',)), [('Constant', (3, 7, 3, 8), 1, None)], [])], None, None, [])], []),
('Module', [('AsyncFunctionDef', (4, 0, 4, 19), 'f', ('arguments', [], [], None, [], [], None, []), [('Pass', (4, 15, 4, 19))], [('Name', (1, 1, 1, 6), 'deco1', ('Load',)), ('Call', (2, 1, 2, 8), ('Name', (2, 1, 2, 6), 'deco2', ('Load',)), [], []), ('Call', (3, 1, 3, 9), ('Name', (3, 1, 3, 6), 'deco3', ('Load',)), [('Constant', (3, 7, 3, 8), 1, None)], [])], None, None, [])], []),
('Module', [('ClassDef', (4, 0, 4, 13), 'C', [], [], [('Pass', (4, 9, 4, 13))], [('Name', (1, 1, 1, 6), 'deco1', ('Load',)), ('Call', (2, 1, 2, 8), ('Name', (2, 1, 2, 6), 'deco2', ('Load',)), [], []), ('Call', (3, 1, 3, 9), ('Name', (3, 1, 3, 6), 'deco3', ('Load',)), [('Constant', (3, 7, 3, 8), 1, None)], [])], [])], []),
('Module', [('FunctionDef', (2, 0, 2, 13), 'f', ('arguments', [], [], None, [], [], None, []), [('Pass', (2, 9, 2, 13))], [('Call', (1, 1, 1, 19), ('Name', (1, 1, 1, 5), 'deco', ('Load',)), [('GeneratorExp', (1, 5, 1, 19), ('Name', (1, 6, 1, 7), 'a', ('Load',)), [('comprehension', ('Name', (1, 12, 1, 13), 'a', ('Store',)), ('Name', (1, 17, 1, 18), 'b', ('Load',)), [], 0)])], [])], None, None, [])], []),
('Module', [('FunctionDef', (2, 0, 2, 13), 'f', ('arguments', [], [], None, [], [], None, []), [('Pass', (2, 9, 2, 13))], [('Attribute', (1, 1, 1, 6), ('Attribute', (1, 1, 1, 4), ('Name', (1, 1, 1, 2), 'a', ('Load',)), 'b', ('Load',)), 'c', ('Load',))], None, None, [])], []),
('Module', [('Expr', (1, 0, 1, 8), ('NamedExpr', (1, 1, 1, 7), ('Name', (1, 1, 1, 2), 'a', ('Store',)), ('Constant', (1, 6, 1, 7), 1, None)))], []),
('Module', [('If', (1, 0, 1, 19), ('NamedExpr', (1, 3, 1, 13), ('Name', (1, 3, 1, 4), 'a', ('Store',)), ('Call', (1, 8, 1, 13), ('Name', (1, 8, 1, 11), 'foo', ('Load',)), [], [])), [('Pass', (1, 15, 1, 19))], [])], []),
('Module', [('While', (1, 0, 1, 22), ('NamedExpr', (1, 6, 1, 16), ('Name', (1, 6, 1, 7), 'a', ('Store',)), ('Call', (1, 11, 1, 16), ('Name', (1, 11, 1, 14), 'foo', ('Load',)), [], [])), [('Pass', (1, 18, 1, 22))], [])], []),
('Module', [('FunctionDef', (1, 0, 1, 18), 'f', ('arguments', [('arg', (1, 6, 1, 7), 'a', None, None)], [], None, [], [], None, []), [('Pass', (1, 14, 1, 18))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 26), 'f', ('arguments', [('arg', (1, 6, 1, 7), 'a', None, None)], [('arg', (1, 12, 1, 13), 'c', None, None), ('arg', (1, 15, 1, 16), 'd', None, None), ('arg', (1, 18, 1, 19), 'e', None, None)], None, [], [], None, []), [('Pass', (1, 22, 1, 26))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 29), 'f', ('arguments', [('arg', (1, 6, 1, 7), 'a', None, None)], [('arg', (1, 12, 1, 13), 'c', None, None)], None, [('arg', (1, 18, 1, 19), 'd', None, None), ('arg', (1, 21, 1, 22), 'e', None, None)], [None, None], None, []), [('Pass', (1, 25, 1, 29))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 39), 'f', ('arguments', [('arg', (1, 6, 1, 7), 'a', None, None)], [('arg', (1, 12, 1, 13), 'c', None, None)], None, [('arg', (1, 18, 1, 19), 'd', None, None), ('arg', (1, 21, 1, 22), 'e', None, None)], [None, None], ('arg', (1, 26, 1, 32), 'kwargs', None, None), []), [('Pass', (1, 35, 1, 39))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 20), 'f', ('arguments', [('arg', (1, 6, 1, 7), 'a', None, None)], [], None, [], [], None, [('Constant', (1, 8, 1, 9), 1, None)]), [('Pass', (1, 16, 1, 20))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 29), 'f', ('arguments', [('arg', (1, 6, 1, 7), 'a', None, None)], [('arg', (1, 14, 1, 15), 'b', None, None), ('arg', (1, 19, 1, 20), 'c', None, None)], None, [], [], None, [('Constant', (1, 8, 1, 9), 1, None), ('Constant', (1, 16, 1, 17), 2, None), ('Constant', (1, 21, 1, 22), 4, None)]), [('Pass', (1, 25, 1, 29))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 32), 'f', ('arguments', [('arg', (1, 6, 1, 7), 'a', None, None)], [('arg', (1, 14, 1, 15), 'b', None, None)], None, [('arg', (1, 22, 1, 23), 'c', None, None)], [('Constant', (1, 24, 1, 25), 4, None)], None, [('Constant', (1, 8, 1, 9), 1, None), ('Constant', (1, 16, 1, 17), 2, None)]), [('Pass', (1, 28, 1, 32))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 30), 'f', ('arguments', [('arg', (1, 6, 1, 7), 'a', None, None)], [('arg', (1, 14, 1, 15), 'b', None, None)], None, [('arg', (1, 22, 1, 23), 'c', None, None)], [None], None, [('Constant', (1, 8, 1, 9), 1, None), ('Constant', (1, 16, 1, 17), 2, None)]), [('Pass', (1, 26, 1, 30))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 42), 'f', ('arguments', [('arg', (1, 6, 1, 7), 'a', None, None)], [('arg', (1, 14, 1, 15), 'b', None, None)], None, [('arg', (1, 22, 1, 23), 'c', None, None)], [('Constant', (1, 24, 1, 25), 4, None)], ('arg', (1, 29, 1, 35), 'kwargs', None, None), [('Constant', (1, 8, 1, 9), 1, None), ('Constant', (1, 16, 1, 17), 2, None)]), [('Pass', (1, 38, 1, 42))], [], None, None, [])], []),
('Module', [('FunctionDef', (1, 0, 1, 40), 'f', ('arguments', [('arg', (1, 6, 1, 7), 'a', None, None)], [('arg', (1, 14, 1, 15), 'b', None, None)], None, [('arg', (1, 22, 1, 23), 'c', None, None)], [None], ('arg', (1, 27, 1, 33), 'kwargs', None, None), [('Constant', (1, 8, 1, 9), 1, None), ('Constant', (1, 16, 1, 17), 2, None)]), [('Pass', (1, 36, 1, 40))], [], None, None, [])], []),
('Module', [('TypeAlias', (1, 0, 1, 12), ('Name', (1, 5, 1, 6), 'X', ('Store',)), [], ('Name', (1, 9, 1, 12), 'int', ('Load',)))], []),
('Module', [('TypeAlias', (1, 0, 1, 15), ('Name', (1, 5, 1, 6), 'X', ('Store',)), [('TypeVar', (1, 7, 1, 8), 'T', None, None)], ('Name', (1, 12, 1, 15), 'int', ('Load',)))], []),
('Module', [('TypeAlias', (1, 0, 1, 32), ('Name', (1, 5, 1, 6), 'X', ('Store',)), [('TypeVar', (1, 7, 1, 8), 'T', None, None), ('TypeVarTuple', (1, 10, 1, 13), 'Ts', None), ('ParamSpec', (1, 15, 1, 18), 'P', None)], ('Tuple', (1, 22, 1, 32), [('Name', (1, 23, 1, 24), 'T', ('Load',)), ('Name', (1, 26, 1, 28), 'Ts', ('Load',)), ('Name', (1, 30, 1, 31), 'P', ('Load',))], ('Load',)))], []),
('Module', [('TypeAlias', (1, 0, 1, 37), ('Name', (1, 5, 1, 6), 'X', ('Store',)), [('TypeVar', (1, 7, 1, 13), 'T', ('Name', (1, 10, 1, 13), 'int', ('Load',)), None), ('TypeVarTuple', (1, 15, 1, 18), 'Ts', None), ('ParamSpec', (1, 20, 1, 23), 'P', None)], ('Tuple', (1, 27, 1, 37), [('Name', (1, 28, 1, 29), 'T', ('Load',)), ('Name', (1, 31, 1, 33), 'Ts', ('Load',)), ('Name', (1, 35, 1, 36), 'P', ('Load',))], ('Load',)))], []),
('Module', [('TypeAlias', (1, 0, 1, 44), ('Name', (1, 5, 1, 6), 'X', ('Store',)), [('TypeVar', (1, 7, 1, 20), 'T', ('Tuple', (1, 10, 1, 20), [('Name', (1, 11, 1, 14), 'int', ('Load',)), ('Name', (1, 16, 1, 19), 'str', ('Load',))], ('Load',)), None), ('TypeVarTuple', (1, 22, 1, 25), 'Ts', None), ('ParamSpec', (1, 27, 1, 30), 'P', None)], ('Tuple', (1, 34, 1, 44), [('Name', (1, 35, 1, 36), 'T', ('Load',)), ('Name', (1, 38, 1, 40), 'Ts', ('Load',)), ('Name', (1, 42, 1, 43), 'P', ('Load',))], ('Load',)))], []),
('Module', [('TypeAlias', (1, 0, 1, 48), ('Name', (1, 5, 1, 6), 'X', ('Store',)), [('TypeVar', (1, 7, 1, 17), 'T', ('Name', (1, 10, 1, 13), 'int', ('Load',)), ('Constant', (1, 16, 1, 17), 1, None)), ('TypeVarTuple', (1, 19, 1, 26), 'Ts', ('Constant', (1, 25, 1, 26), 2, None)), ('ParamSpec', (1, 28, 1, 34), 'P', ('Constant', (1, 33, 1, 34), 3, None))], ('Tuple', (1, 38, 1, 48), [('Name', (1, 39, 1, 40), 'T', ('Load',)), ('Name', (1, 42, 1, 44), 'Ts', ('Load',)), ('Name', (1, 46, 1, 47), 'P', ('Load',))], ('Load',)))], []),
('Module', [('ClassDef', (1, 0, 1, 16), 'X', [], [], [('Pass', (1, 12, 1, 16))], [], [('TypeVar', (1, 8, 1, 9), 'T', None, None)])], []),
('Module', [('ClassDef', (1, 0, 1, 26), 'X', [], [], [('Pass', (1, 22, 1, 26))], [], [('TypeVar', (1, 8, 1, 9), 'T', None, None), ('TypeVarTuple', (1, 11, 1, 14), 'Ts', None), ('ParamSpec', (1, 16, 1, 19), 'P', None)])], []),
('Module', [('ClassDef', (1, 0, 1, 31), 'X', [], [], [('Pass', (1, 27, 1, 31))], [], [('TypeVar', (1, 8, 1, 14), 'T', ('Name', (1, 11, 1, 14), 'int', ('Load',)), None), ('TypeVarTuple', (1, 16, 1, 19), 'Ts', None), ('ParamSpec', (1, 21, 1, 24), 'P', None)])], []),
('Module', [('ClassDef', (1, 0, 1, 38), 'X', [], [], [('Pass', (1, 34, 1, 38))], [], [('TypeVar', (1, 8, 1, 21), 'T', ('Tuple', (1, 11, 1, 21), [('Name', (1, 12, 1, 15), 'int', ('Load',)), ('Name', (1, 17, 1, 20), 'str', ('Load',))], ('Load',)), None), ('TypeVarTuple', (1, 23, 1, 26), 'Ts', None), ('ParamSpec', (1, 28, 1, 31), 'P', None)])], []),
('Module', [('ClassDef', (1, 0, 1, 43), 'X', [], [], [('Pass', (1, 39, 1, 43))], [], [('TypeVar', (1, 8, 1, 18), 'T', ('Name', (1, 11, 1, 14), 'int', ('Load',)), ('Constant', (1, 17, 1, 18), 1, None)), ('TypeVarTuple', (1, 20, 1, 27), 'Ts', ('Constant', (1, 26, 1, 27), 2, None)), ('ParamSpec', (1, 29, 1, 36), 'P', ('Constant', (1, 35, 1, 36), 3, None))])], []),
('Module', [('FunctionDef', (1, 0, 1, 16), 'f', ('arguments', [], [], None, [], [], None, []), [('Pass', (1, 12, 1, 16))], [], None, None, [('TypeVar', (1, 6, 1, 7), 'T', None, None)])], []),
('Module', [('FunctionDef', (1, 0, 1, 26), 'f', ('arguments', [], [], None, [], [], None, []), [('Pass', (1, 22, 1, 26))], [], None, None, [('TypeVar', (1, 6, 1, 7), 'T', None, None), ('TypeVarTuple', (1, 9, 1, 12), 'Ts', None), ('ParamSpec', (1, 14, 1, 17), 'P', None)])], []),
('Module', [('FunctionDef', (1, 0, 1, 31), 'f', ('arguments', [], [], None, [], [], None, []), [('Pass', (1, 27, 1, 31))], [], None, None, [('TypeVar', (1, 6, 1, 12), 'T', ('Name', (1, 9, 1, 12), 'int', ('Load',)), None), ('TypeVarTuple', (1, 14, 1, 17), 'Ts', None), ('ParamSpec', (1, 19, 1, 22), 'P', None)])], []),
('Module', [('FunctionDef', (1, 0, 1, 38), 'f', ('arguments', [], [], None, [], [], None, []), [('Pass', (1, 34, 1, 38))], [], None, None, [('TypeVar', (1, 6, 1, 19), 'T', ('Tuple', (1, 9, 1, 19), [('Name', (1, 10, 1, 13), 'int', ('Load',)), ('Name', (1, 15, 1, 18), 'str', ('Load',))], ('Load',)), None), ('TypeVarTuple', (1, 21, 1, 24), 'Ts', None), ('ParamSpec', (1, 26, 1, 29), 'P', None)])], []),
('Module', [('FunctionDef', (1, 0, 1, 43), 'f', ('arguments', [], [], None, [], [], None, []), [('Pass', (1, 39, 1, 43))], [], None, None, [('TypeVar', (1, 6, 1, 16), 'T', ('Name', (1, 9, 1, 12), 'int', ('Load',)), ('Constant', (1, 15, 1, 16), 1, None)), ('TypeVarTuple', (1, 18, 1, 25), 'Ts', ('Constant', (1, 24, 1, 25), 2, None)), ('ParamSpec', (1, 27, 1, 34), 'P', ('Constant', (1, 33, 1, 34), 3, None))])], []),
('Module', [('Match', (1, 0, 3, 6), ('Name', (1, 6, 1, 7), 'x', ('Load',)), [('match_case', ('MatchValue', (2, 6, 2, 7), ('Constant', (2, 6, 2, 7), 1, None)), None, [('Pass', (3, 2, 3, 6))])])], []),
('Module', [('Match', (1, 0, 5, 6), ('Name', (1, 6, 1, 7), 'x', ('Load',)), [('match_case', ('MatchValue', (2, 6, 2, 7), ('Constant', (2, 6, 2, 7), 1, None)), None, [('Pass', (3, 2, 3, 6))]), ('match_case', ('MatchAs', (4, 6, 4, 7), None, None), None, [('Pass', (5, 2, 5, 6))])])], []),
]
single_results = [
('Interactive', [('Expr', (1, 0, 1, 3), ('BinOp', (1, 0, 1, 3), ('Constant', (1, 0, 1, 1), 1, None), ('Add',), ('Constant', (1, 2, 1, 3), 2, None)))]),
]
eval_results = [
('Expression', ('Constant', (1, 0, 1, 4), None, None)),
('Expression', ('Constant', (1, 0, 1, 4), True, None)),
('Expression', ('Constant', (1, 0, 1, 5), False, None)),
('Expression', ('BoolOp', (1, 0, 1, 7), ('And',), [('Name', (1, 0, 1, 1), 'a', ('Load',)), ('Name', (1, 6, 1, 7), 'b', ('Load',))])),
('Expression', ('BoolOp', (1, 0, 1, 6), ('Or',), [('Name', (1, 0, 1, 1), 'a', ('Load',)), ('Name', (1, 5, 1, 6), 'b', ('Load',))])),
('Expression', ('BinOp', (1, 0, 1, 5), ('Name', (1, 0, 1, 1), 'a', ('Load',)), ('Add',), ('Name', (1, 4, 1, 5), 'b', ('Load',)))),
('Expression', ('BinOp', (1, 0, 1, 5), ('Name', (1, 0, 1, 1), 'a', ('Load',)), ('Sub',), ('Name', (1, 4, 1, 5), 'b', ('Load',)))),
('Expression', ('BinOp', (1, 0, 1, 5), ('Name', (1, 0, 1, 1), 'a', ('Load',)), ('Mult',), ('Name', (1, 4, 1, 5), 'b', ('Load',)))),
('Expression', ('BinOp', (1, 0, 1, 5), ('Name', (1, 0, 1, 1), 'a', ('Load',)), ('Div',), ('Name', (1, 4, 1, 5), 'b', ('Load',)))),
('Expression', ('BinOp', (1, 0, 1, 5), ('Name', (1, 0, 1, 1), 'a', ('Load',)), ('MatMult',), ('Name', (1, 4, 1, 5), 'b', ('Load',)))),
('Expression', ('BinOp', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'a', ('Load',)), ('FloorDiv',), ('Name', (1, 5, 1, 6), 'b', ('Load',)))),
('Expression', ('BinOp', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'a', ('Load',)), ('Pow',), ('Name', (1, 5, 1, 6), 'b', ('Load',)))),
('Expression', ('BinOp', (1, 0, 1, 5), ('Name', (1, 0, 1, 1), 'a', ('Load',)), ('Mod',), ('Name', (1, 4, 1, 5), 'b', ('Load',)))),
('Expression', ('BinOp', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'a', ('Load',)), ('RShift',), ('Name', (1, 5, 1, 6), 'b', ('Load',)))),
('Expression', ('BinOp', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'a', ('Load',)), ('LShift',), ('Name', (1, 5, 1, 6), 'b', ('Load',)))),
('Expression', ('BinOp', (1, 0, 1, 5), ('Name', (1, 0, 1, 1), 'a', ('Load',)), ('BitXor',), ('Name', (1, 4, 1, 5), 'b', ('Load',)))),
('Expression', ('BinOp', (1, 0, 1, 5), ('Name', (1, 0, 1, 1), 'a', ('Load',)), ('BitOr',), ('Name', (1, 4, 1, 5), 'b', ('Load',)))),
('Expression', ('BinOp', (1, 0, 1, 5), ('Name', (1, 0, 1, 1), 'a', ('Load',)), ('BitAnd',), ('Name', (1, 4, 1, 5), 'b', ('Load',)))),
('Expression', ('UnaryOp', (1, 0, 1, 5), ('Not',), ('Name', (1, 4, 1, 5), 'v', ('Load',)))),
('Expression', ('UnaryOp', (1, 0, 1, 2), ('UAdd',), ('Name', (1, 1, 1, 2), 'v', ('Load',)))),
('Expression', ('UnaryOp', (1, 0, 1, 2), ('USub',), ('Name', (1, 1, 1, 2), 'v', ('Load',)))),
('Expression', ('UnaryOp', (1, 0, 1, 2), ('Invert',), ('Name', (1, 1, 1, 2), 'v', ('Load',)))),
('Expression', ('Lambda', (1, 0, 1, 11), ('arguments', [], [], None, [], [], None, []), ('Constant', (1, 7, 1, 11), None, None))),
('Expression', ('Dict', (1, 0, 1, 7), [('Constant', (1, 2, 1, 3), 1, None)], [('Constant', (1, 4, 1, 5), 2, None)])),
('Expression', ('Dict', (1, 0, 1, 2), [], [])),
('Expression', ('Set', (1, 0, 1, 7), [('Constant', (1, 1, 1, 5), None, None)])),
('Expression', ('Dict', (1, 0, 5, 6), [('Constant', (2, 6, 2, 7), 1, None)], [('Constant', (4, 10, 4, 11), 2, None)])),
('Expression', ('List', (1, 0, 5, 6), [('Constant', (2, 6, 2, 7), 1, None), ('Constant', (4, 8, 4, 9), 1, None)], ('Load',))),
('Expression', ('Tuple', (1, 0, 4, 6), [('Constant', (2, 6, 2, 7), 1, None)], ('Load',))),
('Expression', ('Set', (1, 0, 5, 6), [('Constant', (2, 6, 2, 7), 1, None), ('Constant', (4, 8, 4, 9), 1, None)])),
('Expression', ('ListComp', (1, 0, 1, 19), ('Name', (1, 1, 1, 2), 'a', ('Load',)), [('comprehension', ('Name', (1, 7, 1, 8), 'b', ('Store',)), ('Name', (1, 12, 1, 13), 'c', ('Load',)), [('Name', (1, 17, 1, 18), 'd', ('Load',))], 0)])),
('Expression', ('GeneratorExp', (1, 0, 1, 19), ('Name', (1, 1, 1, 2), 'a', ('Load',)), [('comprehension', ('Name', (1, 7, 1, 8), 'b', ('Store',)), ('Name', (1, 12, 1, 13), 'c', ('Load',)), [('Name', (1, 17, 1, 18), 'd', ('Load',))], 0)])),
('Expression', ('SetComp', (1, 0, 1, 19), ('Name', (1, 1, 1, 2), 'a', ('Load',)), [('comprehension', ('Name', (1, 7, 1, 8), 'b', ('Store',)), ('Name', (1, 12, 1, 13), 'c', ('Load',)), [('Name', (1, 17, 1, 18), 'd', ('Load',))], 0)])),
('Expression', ('DictComp', (1, 0, 1, 25), ('Name', (1, 1, 1, 2), 'k', ('Load',)), ('Name', (1, 4, 1, 5), 'v', ('Load',)), [('comprehension', ('Tuple', (1, 10, 1, 14), [('Name', (1, 10, 1, 11), 'k', ('Store',)), ('Name', (1, 13, 1, 14), 'v', ('Store',))], ('Store',)), ('Name', (1, 18, 1, 19), 'c', ('Load',)), [('Name', (1, 23, 1, 24), 'd', ('Load',))], 0)])),
('Expression', ('ListComp', (1, 0, 1, 20), ('Tuple', (1, 1, 1, 6), [('Name', (1, 2, 1, 3), 'a', ('Load',)), ('Name', (1, 4, 1, 5), 'b', ('Load',))], ('Load',)), [('comprehension', ('Tuple', (1, 11, 1, 14), [('Name', (1, 11, 1, 12), 'a', ('Store',)), ('Name', (1, 13, 1, 14), 'b', ('Store',))], ('Store',)), ('Name', (1, 18, 1, 19), 'c', ('Load',)), [], 0)])),
('Expression', ('ListComp', (1, 0, 1, 22), ('Tuple', (1, 1, 1, 6), [('Name', (1, 2, 1, 3), 'a', ('Load',)), ('Name', (1, 4, 1, 5), 'b', ('Load',))], ('Load',)), [('comprehension', ('Tuple', (1, 11, 1, 16), [('Name', (1, 12, 1, 13), 'a', ('Store',)), ('Name', (1, 14, 1, 15), 'b', ('Store',))], ('Store',)), ('Name', (1, 20, 1, 21), 'c', ('Load',)), [], 0)])),
('Expression', ('ListComp', (1, 0, 1, 22), ('Tuple', (1, 1, 1, 6), [('Name', (1, 2, 1, 3), 'a', ('Load',)), ('Name', (1, 4, 1, 5), 'b', ('Load',))], ('Load',)), [('comprehension', ('List', (1, 11, 1, 16), [('Name', (1, 12, 1, 13), 'a', ('Store',)), ('Name', (1, 14, 1, 15), 'b', ('Store',))], ('Store',)), ('Name', (1, 20, 1, 21), 'c', ('Load',)), [], 0)])),
('Expression', ('SetComp', (1, 0, 1, 20), ('Tuple', (1, 1, 1, 6), [('Name', (1, 2, 1, 3), 'a', ('Load',)), ('Name', (1, 4, 1, 5), 'b', ('Load',))], ('Load',)), [('comprehension', ('Tuple', (1, 11, 1, 14), [('Name', (1, 11, 1, 12), 'a', ('Store',)), ('Name', (1, 13, 1, 14), 'b', ('Store',))], ('Store',)), ('Name', (1, 18, 1, 19), 'c', ('Load',)), [], 0)])),
('Expression', ('SetComp', (1, 0, 1, 22), ('Tuple', (1, 1, 1, 6), [('Name', (1, 2, 1, 3), 'a', ('Load',)), ('Name', (1, 4, 1, 5), 'b', ('Load',))], ('Load',)), [('comprehension', ('Tuple', (1, 11, 1, 16), [('Name', (1, 12, 1, 13), 'a', ('Store',)), ('Name', (1, 14, 1, 15), 'b', ('Store',))], ('Store',)), ('Name', (1, 20, 1, 21), 'c', ('Load',)), [], 0)])),
('Expression', ('SetComp', (1, 0, 1, 22), ('Tuple', (1, 1, 1, 6), [('Name', (1, 2, 1, 3), 'a', ('Load',)), ('Name', (1, 4, 1, 5), 'b', ('Load',))], ('Load',)), [('comprehension', ('List', (1, 11, 1, 16), [('Name', (1, 12, 1, 13), 'a', ('Store',)), ('Name', (1, 14, 1, 15), 'b', ('Store',))], ('Store',)), ('Name', (1, 20, 1, 21), 'c', ('Load',)), [], 0)])),
('Expression', ('GeneratorExp', (1, 0, 1, 20), ('Tuple', (1, 1, 1, 6), [('Name', (1, 2, 1, 3), 'a', ('Load',)), ('Name', (1, 4, 1, 5), 'b', ('Load',))], ('Load',)), [('comprehension', ('Tuple', (1, 11, 1, 14), [('Name', (1, 11, 1, 12), 'a', ('Store',)), ('Name', (1, 13, 1, 14), 'b', ('Store',))], ('Store',)), ('Name', (1, 18, 1, 19), 'c', ('Load',)), [], 0)])),
('Expression', ('GeneratorExp', (1, 0, 1, 22), ('Tuple', (1, 1, 1, 6), [('Name', (1, 2, 1, 3), 'a', ('Load',)), ('Name', (1, 4, 1, 5), 'b', ('Load',))], ('Load',)), [('comprehension', ('Tuple', (1, 11, 1, 16), [('Name', (1, 12, 1, 13), 'a', ('Store',)), ('Name', (1, 14, 1, 15), 'b', ('Store',))], ('Store',)), ('Name', (1, 20, 1, 21), 'c', ('Load',)), [], 0)])),
('Expression', ('GeneratorExp', (1, 0, 1, 22), ('Tuple', (1, 1, 1, 6), [('Name', (1, 2, 1, 3), 'a', ('Load',)), ('Name', (1, 4, 1, 5), 'b', ('Load',))], ('Load',)), [('comprehension', ('List', (1, 11, 1, 16), [('Name', (1, 12, 1, 13), 'a', ('Store',)), ('Name', (1, 14, 1, 15), 'b', ('Store',))], ('Store',)), ('Name', (1, 20, 1, 21), 'c', ('Load',)), [], 0)])),
('Expression', ('Compare', (1, 0, 1, 9), ('Constant', (1, 0, 1, 1), 1, None), [('Lt',), ('Lt',)], [('Constant', (1, 4, 1, 5), 2, None), ('Constant', (1, 8, 1, 9), 3, None)])),
('Expression', ('Compare', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'a', ('Load',)), [('Eq',)], [('Name', (1, 5, 1, 6), 'b', ('Load',))])),
('Expression', ('Compare', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'a', ('Load',)), [('LtE',)], [('Name', (1, 5, 1, 6), 'b', ('Load',))])),
('Expression', ('Compare', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'a', ('Load',)), [('GtE',)], [('Name', (1, 5, 1, 6), 'b', ('Load',))])),
('Expression', ('Compare', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'a', ('Load',)), [('NotEq',)], [('Name', (1, 5, 1, 6), 'b', ('Load',))])),
('Expression', ('Compare', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'a', ('Load',)), [('Is',)], [('Name', (1, 5, 1, 6), 'b', ('Load',))])),
('Expression', ('Compare', (1, 0, 1, 10), ('Name', (1, 0, 1, 1), 'a', ('Load',)), [('IsNot',)], [('Name', (1, 9, 1, 10), 'b', ('Load',))])),
('Expression', ('Compare', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'a', ('Load',)), [('In',)], [('Name', (1, 5, 1, 6), 'b', ('Load',))])),
('Expression', ('Compare', (1, 0, 1, 10), ('Name', (1, 0, 1, 1), 'a', ('Load',)), [('NotIn',)], [('Name', (1, 9, 1, 10), 'b', ('Load',))])),
('Expression', ('Call', (1, 0, 1, 3), ('Name', (1, 0, 1, 1), 'f', ('Load',)), [], [])),
('Expression', ('Call', (1, 0, 1, 17), ('Name', (1, 0, 1, 1), 'f', ('Load',)), [('Constant', (1, 2, 1, 3), 1, None), ('Constant', (1, 4, 1, 5), 2, None), ('Starred', (1, 10, 1, 12), ('Name', (1, 11, 1, 12), 'd', ('Load',)), ('Load',))], [('keyword', (1, 6, 1, 9), 'c', ('Constant', (1, 8, 1, 9), 3, None)), ('keyword', (1, 13, 1, 16), None, ('Name', (1, 15, 1, 16), 'e', ('Load',)))])),
('Expression', ('Call', (1, 0, 1, 10), ('Name', (1, 0, 1, 1), 'f', ('Load',)), [('Starred', (1, 2, 1, 9), ('List', (1, 3, 1, 9), [('Constant', (1, 4, 1, 5), 0, None), ('Constant', (1, 7, 1, 8), 1, None)], ('Load',)), ('Load',))], [])),
('Expression', ('Call', (1, 0, 1, 15), ('Name', (1, 0, 1, 1), 'f', ('Load',)), [('GeneratorExp', (1, 1, 1, 15), ('Name', (1, 2, 1, 3), 'a', ('Load',)), [('comprehension', ('Name', (1, 8, 1, 9), 'a', ('Store',)), ('Name', (1, 13, 1, 14), 'b', ('Load',)), [], 0)])], [])),
('Expression', ('Constant', (1, 0, 1, 2), 10, None)),
('Expression', ('Constant', (1, 0, 1, 2), 1j, None)),
('Expression', ('Constant', (1, 0, 1, 8), 'string', None)),
('Expression', ('Attribute', (1, 0, 1, 3), ('Name', (1, 0, 1, 1), 'a', ('Load',)), 'b', ('Load',))),
('Expression', ('Subscript', (1, 0, 1, 6), ('Name', (1, 0, 1, 1), 'a', ('Load',)), ('Slice', (1, 2, 1, 5), ('Name', (1, 2, 1, 3), 'b', ('Load',)), ('Name', (1, 4, 1, 5), 'c', ('Load',)), None), ('Load',))),
('Expression', ('Name', (1, 0, 1, 1), 'v', ('Load',))),
('Expression', ('List', (1, 0, 1, 7), [('Constant', (1, 1, 1, 2), 1, None), ('Constant', (1, 3, 1, 4), 2, None), ('Constant', (1, 5, 1, 6), 3, None)], ('Load',))),
('Expression', ('List', (1, 0, 1, 2), [], ('Load',))),
('Expression', ('Tuple', (1, 0, 1, 5), [('Constant', (1, 0, 1, 1), 1, None), ('Constant', (1, 2, 1, 3), 2, None), ('Constant', (1, 4, 1, 5), 3, None)], ('Load',))),
('Expression', ('Tuple', (1, 0, 1, 7), [('Constant', (1, 1, 1, 2), 1, None), ('Constant', (1, 3, 1, 4), 2, None), ('Constant', (1, 5, 1, 6), 3, None)], ('Load',))),
('Expression', ('Tuple', (1, 0, 1, 2), [], ('Load',))),
('Expression', ('Call', (1, 0, 1, 17), ('Attribute', (1, 0, 1, 7), ('Attribute', (1, 0, 1, 5), ('Attribute', (1, 0, 1, 3), ('Name', (1, 0, 1, 1), 'a', ('Load',)), 'b', ('Load',)), 'c', ('Load',)), 'd', ('Load',)), [('Subscript', (1, 8, 1, 16), ('Attribute', (1, 8, 1, 11), ('Name', (1, 8, 1, 9), 'a', ('Load',)), 'b', ('Load',)), ('Slice', (1, 12, 1, 15), ('Constant', (1, 12, 1, 13), 1, None), ('Constant', (1, 14, 1, 15), 2, None), None), ('Load',))], [])),
('Expression', ('Subscript', (1, 0, 1, 7), ('List', (1, 0, 1, 3), [('Constant', (1, 1, 1, 2), 5, None)], ('Load',)), ('Slice', (1, 4, 1, 6), ('Constant', (1, 4, 1, 5), 1, None), None, None), ('Load',))),
('Expression', ('Subscript', (1, 0, 1, 7), ('List', (1, 0, 1, 3), [('Constant', (1, 1, 1, 2), 5, None)], ('Load',)), ('Slice', (1, 4, 1, 6), None, ('Constant', (1, 5, 1, 6), 1, None), None), ('Load',))),
('Expression', ('Subscript', (1, 0, 1, 8), ('List', (1, 0, 1, 3), [('Constant', (1, 1, 1, 2), 5, None)], ('Load',)), ('Slice', (1, 4, 1, 7), None, None, ('Constant', (1, 6, 1, 7), 1, None)), ('Load',))),
('Expression', ('Subscript', (1, 0, 1, 10), ('List', (1, 0, 1, 3), [('Constant', (1, 1, 1, 2), 5, None)], ('Load',)), ('Slice', (1, 4, 1, 9), ('Constant', (1, 4, 1, 5), 1, None), ('Constant', (1, 6, 1, 7), 1, None), ('Constant', (1, 8, 1, 9), 1, None)), ('Load',))),
('Expression', ('IfExp', (1, 0, 1, 21), ('Name', (1, 9, 1, 10), 'x', ('Load',)), ('Call', (1, 0, 1, 5), ('Name', (1, 0, 1, 3), 'foo', ('Load',)), [], []), ('Call', (1, 16, 1, 21), ('Name', (1, 16, 1, 19), 'bar', ('Load',)), [], []))),
('Expression', ('JoinedStr', (1, 0, 1, 6), [('FormattedValue', (1, 2, 1, 5), ('Name', (1, 3, 1, 4), 'a', ('Load',)), -1, None)])),
('Expression', ('JoinedStr', (1, 0, 1, 10), [('FormattedValue', (1, 2, 1, 9), ('Name', (1, 3, 1, 4), 'a', ('Load',)), -1, ('JoinedStr', (1, 4, 1, 8), [('Constant', (1, 5, 1, 8), '.2f', None)]))])),
('Expression', ('JoinedStr', (1, 0, 1, 8), [('FormattedValue', (1, 2, 1, 7), ('Name', (1, 3, 1, 4), 'a', ('Load',)), 114, None)])),
('Expression', ('JoinedStr', (1, 0, 1, 11), [('Constant', (1, 2, 1, 6), 'foo(', None), ('FormattedValue', (1, 6, 1, 9), ('Name', (1, 7, 1, 8), 'a', ('Load',)), -1, None), ('Constant', (1, 9, 1, 10), ')', None)])),
]
main()
