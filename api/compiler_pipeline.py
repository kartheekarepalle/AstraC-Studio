"""
Full compiler visualization pipeline -- 6 phases.
Each phase produces: role, description, output, errors.
If a phase has errors the remaining phases are skipped.

JSON response flat keys:
  tokens, syntax_tree, semantic_tree, symbol_table,
  ir, optimized_ir, assembly, errors, phases (metadata)
"""
import re
from typing import Dict, Any, List, Tuple, Optional

# -- C99 keywords --
C_KEYWORDS = {
    'auto','break','case','char','const','continue','default','do',
    'double','else','enum','extern','float','for','goto','if',
    'inline','int','long','register','restrict','return','short',
    'signed','sizeof','static','struct','switch','typedef','union',
    'unsigned','void','volatile','while','_Bool','_Complex','_Imaginary',
}

# =====================================================================
#  PHASE 1 -- Lexical Analysis
# =====================================================================
PHASE1_ROLE = "Lexical Analysis (Scanner / Tokenizer)"
PHASE1_DESC = (
    "Scans the raw source code character by character and converts it "
    "into a flat stream of tokens. Each token carries a type "
    "(KEYWORD, ID, NUMBER, OP ...), the matched text, and the source "
    "line number. Invalid characters are reported as errors."
)

def phase_lexical(source: str) -> Dict[str, Any]:
    token_spec = [
        ('PP_DIRECTIVE', r'\#[^\n]*'),
        ('COMMENT_LINE', r'//[^\n]*'),
        ('COMMENT_BLOCK', r'/\*[\s\S]*?\*/'),
        ('NUMBER',   r'\d+(\.\d+)?'),
        ('STRING',   r'"([^"\\]|\\.)*"'),
        ('CHAR_LIT', r"'([^'\\]|\\.)*'"),
        ('ID',       r'[A-Za-z_]\w*'),
        ('MULTI_OP', r'(==|!=|<=|>=|&&|\|\||\<\<|>>|\+\+|--|->|\+=|-=|\*=|/=|%=|&=|\|=|\^=)'),
        ('OP',       r'[+\-*/%&|^~!<>]'),
        ('ASSIGN',   r'='),
        ('SEMICOLON', r';'),
        ('COMMA',    r','),
        ('LPAREN',   r'\('),
        ('RPAREN',   r'\)'),
        ('LBRACE',   r'\{'),
        ('RBRACE',   r'\}'),
        ('LBRACK',   r'\['),
        ('RBRACK',   r'\]'),
        ('DOT',      r'\.'),
        ('COLON',    r':'),
        ('QUESTION', r'\?'),
        ('HASH',     r'\#'),
        ('SKIP',     r'[ \t]+'),
        ('NEWLINE',  r'\n'),
        ('MISMATCH', r'.'),
    ]
    tok_regex = '|'.join(f'(?P<{n}>{p})' for n, p in token_spec)
    tokens, errors = [], []
    line_num = 1
    for mo in re.finditer(tok_regex, source):
        kind, value = mo.lastgroup, mo.group()
        col = mo.start() - source.rfind('\n', 0, mo.start())
        if kind == 'NEWLINE':
            line_num += 1
            continue
        if kind in ('SKIP', 'PP_DIRECTIVE', 'COMMENT_LINE', 'COMMENT_BLOCK', 'HASH'):
            line_num += value.count('\n')
            continue
        if kind == 'MISMATCH':
            errors.append({
                'message': f"Invalid character '{value}' at line {line_num}, col {col}",
                'line': line_num, 'col': col, 'char': value,
            })
            continue
        if kind == 'ID' and value in C_KEYWORDS:
            kind = 'KEYWORD'
        if kind == 'MULTI_OP':
            kind = 'OP'
        tokens.append({'type': kind, 'value': value, 'line': line_num})
    return {'tokens': tokens, 'errors': errors}


# =====================================================================
#  PHASE 2 -- Syntax Analysis (Parse Tree with left / right children)
# =====================================================================
PHASE2_ROLE = "Syntax Analysis (Parser)"
PHASE2_DESC = (
    "Validates the token stream against C grammar rules using a "
    "recursive-descent parser and builds a Syntax Tree (Parse Tree). "
    "Each interior node has a label, an optional value, and explicit "
    "'left' and 'right' children (binary layout). Sequences of "
    "statements use right-chaining (linked-list style). Grammar "
    "violations are reported as errors."
)


def _nd(label, value='', left=None, right=None, children=None):
    """Create a tree node with explicit left/right children."""
    n = {'label': label}
    if value:
        n['value'] = value
    if left is not None:
        n['left'] = left
    if right is not None:
        n['right'] = right
    if children is not None:
        n['children'] = children
    return n


class _Parser:
    """Recursive-descent parser producing a tree with left/right children."""

    TYPE_KW = {
        'int', 'float', 'double', 'char', 'void', 'long', 'short',
        'unsigned', 'signed', 'struct', 'union', 'enum', 'const',
        'static', 'extern', 'register', 'volatile', 'inline', '_Bool',
    }

    def __init__(self, tokens):
        self.toks = [(t['type'], t['value'], t.get('line', 0)) for t in tokens]
        self.pos = 0
        self.errors = []

    # helpers
    def _cur(self):
        return self.toks[self.pos] if self.pos < len(self.toks) else ('EOF', '', 0)

    def _peek(self, off=1):
        i = self.pos + off
        return self.toks[i] if i < len(self.toks) else ('EOF', '', 0)

    def _eat(self, kind=None, val=None):
        t = self._cur()
        if kind and t[0] != kind:
            self.errors.append(f"Expected {kind} but got {t[0]} '{t[1]}' at line {t[2]}")
            return t
        if val and t[1] != val:
            self.errors.append(f"Expected '{val}' but got '{t[1]}' at line {t[2]}")
            return t
        self.pos += 1
        return t

    def _match(self, kind, val=None):
        t = self._cur()
        if t[0] != kind:
            return False
        if val is not None and t[1] != val:
            return False
        return True

    def _is_type(self):
        return self._cur()[0] == 'KEYWORD' and self._cur()[1] in self.TYPE_KW

    # program
    def build(self):
        root = None
        last = None
        while self._cur()[0] != 'EOF':
            nd = self._top_level()
            if nd is None:
                self.pos += 1
                continue
            if root is None:
                root = _nd('Program', '', left=nd)
                last = root
            else:
                link = _nd('Program', '', left=nd)
                last['right'] = link
                last = link
        return root or _nd('Program')

    def _top_level(self):
        if self._is_type():
            return self._decl_or_func()
        return None

    def _decl_or_func(self):
        start = self.pos
        ts = self._consume_type()
        while self._cur()[1] == '*':
            ts += '*'
            self._eat()
        if not self._match('ID'):
            self.pos = start + 1
            return None
        name = self._eat('ID')[1]
        if self._match('LPAREN'):
            return self._func_def(ts, name)
        return self._var_decl(ts, name)

    def _consume_type(self):
        parts = []
        while self._is_type():
            parts.append(self._eat()[1])
        return ' '.join(parts) or 'int'

    # function
    def _func_def(self, ret, name):
        self._eat('LPAREN')
        params = self._param_list()
        self._eat('RPAREN')
        if self._match('LBRACE'):
            body = self._block()
        else:
            self._eat('SEMICOLON')
            body = _nd('EmptyBody')
        return _nd('FunctionDef', f'{ret} {name}', left=params, right=body)

    def _param_list(self):
        if self._match('RPAREN'):
            return None
        first = self._param()
        if first is None:
            return None
        head = first
        while self._match('COMMA'):
            self._eat()
            nxt = self._param()
            if nxt:
                head = _nd('ParamList', '', left=head, right=nxt)
        return head

    def _param(self):
        if not self._is_type():
            return None
        t = self._consume_type()
        while self._cur()[1] == '*':
            t += '*'
            self._eat()
        n = self._eat('ID')[1] if self._match('ID') else ''
        if self._match('LBRACK'):
            self._eat()
            if self._match('RBRACK'):
                self._eat()
            t += '[]'
        return _nd('Param', f'{t} {n}'.strip())

    # block / statements
    def _block(self):
        self._eat('LBRACE')
        head = None
        tail = None
        while not self._match('RBRACE') and self._cur()[0] != 'EOF':
            s = self._statement()
            if s is None:
                continue
            link = _nd('StmtList', '', left=s)
            if head is None:
                head = link
                tail = link
            else:
                tail['right'] = link
                tail = link
        self._eat('RBRACE')
        return _nd('Block', '', left=head)

    def _statement(self):
        c = self._cur()
        if c[0] == 'KEYWORD':
            kw = c[1]
            if kw == 'return':
                return self._return()
            if kw == 'if':
                return self._if()
            if kw == 'while':
                return self._while()
            if kw == 'for':
                return self._for()
            if kw == 'do':
                return self._do_while()
            if kw in ('break', 'continue'):
                self._eat()
                self._eat('SEMICOLON')
                return _nd(kw.capitalize() + 'Stmt')
            if kw == 'switch':
                return self._switch()
            if kw in self.TYPE_KW:
                return self._local_decl()
        if c[0] == 'LBRACE':
            return self._block()
        return self._expr_stmt()

    def _return(self):
        self._eat('KEYWORD')
        if self._match('SEMICOLON'):
            self._eat()
            return _nd('ReturnStmt')
        e = self._expression()
        self._eat('SEMICOLON')
        return _nd('ReturnStmt', '', left=e)

    def _if(self):
        self._eat('KEYWORD')
        self._eat('LPAREN')
        cond = self._expression()
        self._eat('RPAREN')
        then = self._stmt_or_block()
        if self._match('KEYWORD', 'else'):
            self._eat()
            els = self._stmt_or_block()
            return _nd('IfStmt', '', left=_nd('Condition', '', left=cond, right=then), right=els)
        return _nd('IfStmt', '', left=cond, right=then)

    def _while(self):
        self._eat('KEYWORD')
        self._eat('LPAREN')
        cond = self._expression()
        self._eat('RPAREN')
        body = self._stmt_or_block()
        return _nd('WhileStmt', '', left=cond, right=body)

    def _for(self):
        self._eat('KEYWORD')
        self._eat('LPAREN')
        init = None
        if not self._match('SEMICOLON'):
            if self._is_type():
                init = self._local_decl()
            else:
                init = self._expression()
                self._eat('SEMICOLON')
        else:
            self._eat()
        cond = None
        if not self._match('SEMICOLON'):
            cond = self._expression()
        self._eat('SEMICOLON')
        upd = None
        if not self._match('RPAREN'):
            upd = self._expression()
        self._eat('RPAREN')
        body = self._stmt_or_block()
        header = _nd('ForHeader', '',
                     left=_nd('ForInit', '', left=init, right=cond),
                     right=upd)
        return _nd('ForStmt', '', left=header, right=body)

    def _do_while(self):
        self._eat('KEYWORD')
        body = self._stmt_or_block()
        self._eat('KEYWORD')  # while
        self._eat('LPAREN')
        cond = self._expression()
        self._eat('RPAREN')
        self._eat('SEMICOLON')
        return _nd('DoWhileStmt', '', left=body, right=cond)

    def _switch(self):
        self._eat('KEYWORD')  # switch
        self._eat('LPAREN')
        expr = self._expression()
        self._eat('RPAREN')
        self._eat('LBRACE')
        cases = []
        default = None
        while not self._match('RBRACE') and self._cur()[0] != 'EOF':
            if self._match('KEYWORD', 'case'):
                self._eat()
                val = self._expression()
                self._eat('COLON')
                stmts = []
                while (not self._match('KEYWORD', 'case')
                       and not self._match('KEYWORD', 'default')
                       and not self._match('RBRACE')
                       and self._cur()[0] != 'EOF'):
                    stmts.append(self._statement())
                cases.append(_nd('Case', '', left=val,
                                 right=_nd('Body', '', children=[s for s in stmts if s])))
            elif self._match('KEYWORD', 'default'):
                self._eat()
                self._eat('COLON')
                stmts = []
                while (not self._match('KEYWORD', 'case')
                       and not self._match('RBRACE')
                       and self._cur()[0] != 'EOF'):
                    stmts.append(self._statement())
                default = _nd('Default', '', children=[s for s in stmts if s])
            else:
                self._eat()
        if self._match('RBRACE'):
            self._eat()
        node = _nd('SwitchStmt', '', left=expr)
        node['cases'] = cases
        node['default'] = default
        return node

    def _stmt_or_block(self):
        if self._match('LBRACE'):
            return self._block()
        return self._statement()

    def _local_decl(self):
        ts = self._consume_type()
        while self._cur()[1] == '*':
            ts += '*'
            self._eat()
        if not self._match('ID'):
            self._skip_semi()
            return _nd('Decl', ts)
        name = self._eat('ID')[1]
        return self._var_decl(ts, name)

    def _var_decl(self, ts, name):
        # Parse first variable (may have array suffix and initializer)
        actual_ts = ts
        if self._match('LBRACK'):
            self._eat()
            sz = ''
            if not self._match('RBRACK'):
                sz = self._cur()[1]
                self._eat()
            self._eat('RBRACK')
            actual_ts = ts + f'[{sz}]'
        init = None
        if self._cur()[1] == '=':
            self._eat()
            if self._match('LBRACE'):
                init = self._init_list()
            else:
                init = self._expression()
        first = _nd('Decl', f'{actual_ts} {name}', left=init)

        # Handle comma-separated declarations: int a, b, c;
        if not self._match('COMMA'):
            self._eat('SEMICOLON')
            return first

        # Build a DeclList chain for multiple declarations
        head = _nd('DeclList', '', left=first)
        tail = head
        while self._match('COMMA'):
            self._eat()  # eat COMMA
            while self._cur()[1] == '*':
                self._eat()  # eat pointer stars
            if not self._match('ID'):
                break
            vname = self._eat('ID')[1]
            vts = ts
            if self._match('LBRACK'):
                self._eat()
                sz = ''
                if not self._match('RBRACK'):
                    sz = self._cur()[1]
                    self._eat()
                self._eat('RBRACK')
                vts = ts + f'[{sz}]'
            vinit = None
            if self._cur()[1] == '=':
                self._eat()
                if self._match('LBRACE'):
                    vinit = self._init_list()
                else:
                    vinit = self._expression()
            link = _nd('DeclList', '', left=_nd('Decl', f'{vts} {vname}', left=vinit))
            tail['right'] = link
            tail = link
        self._eat('SEMICOLON')
        return head

    def _init_list(self):
        self._eat('LBRACE')
        head = None
        tail = None
        while not self._match('RBRACE') and self._cur()[0] != 'EOF':
            if self._match('COMMA'):
                self._eat()
                continue
            e = self._expression()
            link = _nd('InitItem', '', left=e)
            if head is None:
                head = link
                tail = link
            else:
                tail['right'] = link
                tail = link
        self._eat('RBRACE')
        return _nd('InitList', '', left=head)

    def _expr_stmt(self):
        e = self._expression()
        self._eat('SEMICOLON')
        return _nd('ExprStmt', '', left=e)

    # expressions
    def _expression(self):
        return self._assign()

    def _assign(self):
        left = self._lor()
        if self._cur()[1] in ('=', '+=', '-=', '*=', '/=', '%='):
            op = self._eat()[1]
            right = self._assign()
            return _nd('Assign', op, left=left, right=right)
        return left

    def _lor(self):
        n = self._land()
        while self._cur()[1] == '||':
            self._eat()
            r = self._land()
            n = _nd('BinOp', '||', left=n, right=r)
        return n

    def _land(self):
        n = self._eq()
        while self._cur()[1] == '&&':
            self._eat()
            r = self._eq()
            n = _nd('BinOp', '&&', left=n, right=r)
        return n

    def _eq(self):
        n = self._rel()
        while self._cur()[1] in ('==', '!='):
            op = self._eat()[1]
            r = self._rel()
            n = _nd('BinOp', op, left=n, right=r)
        return n

    def _rel(self):
        n = self._add()
        while self._cur()[1] in ('<', '>', '<=', '>='):
            op = self._eat()[1]
            r = self._add()
            n = _nd('BinOp', op, left=n, right=r)
        return n

    def _add(self):
        n = self._mul()
        while self._cur()[1] in ('+', '-'):
            op = self._eat()[1]
            r = self._mul()
            n = _nd('BinOp', op, left=n, right=r)
        return n

    def _mul(self):
        n = self._unary()
        while self._cur()[1] in ('*', '/', '%'):
            op = self._eat()[1]
            r = self._unary()
            n = _nd('BinOp', op, left=n, right=r)
        return n

    def _unary(self):
        c = self._cur()
        if c[1] in ('-', '!', '~', '&', '*') and c[0] == 'OP':
            op = self._eat()[1]
            operand = self._unary()
            return _nd('UnaryOp', op, left=operand)
        if c[0] == 'KEYWORD' and c[1] == 'sizeof':
            self._eat()
            if self._match('LPAREN'):
                self._eat()
                inner = self._expression()
                self._eat('RPAREN')
            else:
                inner = self._unary()
            return _nd('Sizeof', '', left=inner)
        return self._postfix()

    def _postfix(self):
        n = self._primary()
        while True:
            if self._match('LPAREN'):
                self._eat()
                args = self._arg_list()
                self._eat('RPAREN')
                n = _nd('Call', n.get('value', ''), left=args)
            elif self._match('LBRACK'):
                self._eat()
                idx = self._expression()
                self._eat('RBRACK')
                n = _nd('Index', '', left=n, right=idx)
            elif self._cur()[1] in ('++', '--'):
                op = self._eat()[1]
                n = _nd('PostOp', op, left=n)
            else:
                break
        return n

    def _arg_list(self):
        if self._match('RPAREN'):
            return None
        first = self._expression()
        head = _nd('Arg', '', left=first)
        tail = head
        while self._match('COMMA'):
            self._eat()
            a = self._expression()
            link = _nd('Arg', '', left=a)
            tail['right'] = link
            tail = link
        return head

    def _primary(self):
        c = self._cur()
        if c[0] == 'NUMBER':
            self._eat()
            return _nd('Num', c[1])
        if c[0] == 'STRING':
            self._eat()
            return _nd('Str', c[1])
        if c[0] == 'CHAR_LIT':
            self._eat()
            return _nd('Char', c[1])
        if c[0] == 'ID':
            self._eat()
            return _nd('Id', c[1])
        if c[0] == 'LPAREN':
            self._eat()
            e = self._expression()
            self._eat('RPAREN')
            return _nd('Group', '', left=e)
        self._eat()
        return _nd('Tok', c[1])

    def _skip_semi(self):
        while self._cur()[0] != 'EOF' and not self._match('SEMICOLON'):
            self.pos += 1
        if self._match('SEMICOLON'):
            self._eat()


def phase_syntax(tokens):
    try:
        p = _Parser(tokens)
        tree = p.build()
        return {'syntax_tree': tree, 'errors': [{'message': e} for e in p.errors]}
    except Exception as ex:
        return {'syntax_tree': None, 'errors': [{'message': f'Parse error: {ex}'}]}


# =====================================================================
#  ASCII TREE RENDERER  –  textbook N-ary centered format
# =====================================================================
#
# Produces output like you would draw in a notebook:
#
#                  Program
#                     |
#                 int main
#                     |
#                   Block
#                     |
#                 StmtList
#        /    /     |      \      \
#     int a  int b  int sum  ExprStmt  ReturnStmt
#       |      |      |        |          |
#       5     10      +      printf       0
#                    / \       |
#                   a   b     Arg
#                            / \
#                      "str"   sum
#
# Key design decisions
# --------------------
# * StmtList right-chains are **flattened** into one N-ary node so
#   that all statements appear side-by-side under a single StmtList.
# * Arg right-chains are likewise flattened so function arguments
#   sit side-by-side under one Arg node.
# * Single-child links use ``|``, two children use ``/ \``, and
#   three-or-more children use ``/ … | … \``.
# * Every node is shown – nothing is collapsed.
# =====================================================================


def _tree_label(node, show_types=False):
    """Short label for tree display.

    Syntax tree  (show_types=False):  value or label – ``a``, ``+``, ``Program``
    Semantic tree (show_types=True):   value:type     – ``a:int``, ``+:int``

    Structural nodes like FunctionDef show ``label(value)`` so the
    kind is always visible.
    """
    if not node:
        return ''
    lbl = node.get('label', '')
    val = node.get('value', '')
    ti  = node.get('type_info', '') if show_types else ''

    # Structural nodes: always show label, optionally with value
    _STRUCTURAL = {'FunctionDef', 'ForStmt', 'ForHeader', 'ForInit',
                   'WhileStmt', 'DoWhileStmt', 'IfStmt', 'ReturnStmt',
                   'BreakStmt', 'ContinueStmt', 'Block', 'StmtList',
                   'Program', 'Param', 'ExprStmt', 'Decl', 'Call',
                   'SwitchStmt', 'CaseStmt', 'DefaultStmt'}
    if lbl in _STRUCTURAL:
        if val and ti:
            return f"{lbl}({val}:{ti})"
        if val:
            return f"{lbl}({val})"
        if ti:
            return f"{lbl}:{ti}"
        return lbl

    if val and ti:
        return f"{val}:{ti}"
    if val:
        return val
    if ti:
        return f"{lbl}:{ti}"
    return lbl


def render_ascii_tree(node, show_types=False):
    """Render the tree as centered ASCII art (textbook / notebook style).

    Binary ``left``/``right`` nodes whose ``label`` is ``StmtList`` or
    ``Arg`` are flattened into N-ary parent nodes so that the tree looks
    natural rather than right-skewed.
    """

    GAP = 3          # min horizontal gap between adjacent child boxes

    # ── helpers ──────────────────────────────────────────────────────

    def _lbl(nd):
        return _tree_label(nd, show_types)

    def _expand_decllist(dl):
        """Expand a DeclList right-chain into a flat list of Decl nodes."""
        items = []
        cur = dl
        while cur and cur.get('label') == 'DeclList':
            if cur.get('left'):
                items.append(cur['left'])
            cur = cur.get('right')
        if cur:
            items.append(cur)
        return items

    def _children(nd):
        """Return a list of child nodes, flattening right-chains."""
        if nd is None:
            return []
        label = nd.get('label', '')

        # Flatten Program right-chains
        if label == 'Program':
            kids = []
            cur = nd
            while cur and cur.get('label') == 'Program':
                if cur.get('left'):
                    kids.append(cur['left'])
                cur = cur.get('right')
            if cur:
                kids.append(cur)
            return kids

        # Flatten StmtList right-chains, inlining DeclList children
        if label == 'StmtList':
            kids = []
            cur = nd
            while cur and cur.get('label') == 'StmtList':
                child = cur.get('left')
                if child and child.get('label') == 'DeclList':
                    kids.extend(_expand_decllist(child))
                elif child:
                    kids.append(child)
                cur = cur.get('right')
            if cur:
                if cur.get('label') == 'DeclList':
                    kids.extend(_expand_decllist(cur))
                else:
                    kids.append(cur)
            return kids

        # Flatten DeclList right-chains
        if label == 'DeclList':
            return _expand_decllist(nd)

        # Flatten Arg right-chains
        if label == 'Arg':
            kids = []
            cur = nd
            while cur and cur.get('label') == 'Arg':
                if cur.get('left'):
                    kids.append(cur['left'])
                cur = cur.get('right')
            if cur:
                kids.append(cur)
            return kids

        # Flatten ParamList chains
        if label == 'ParamList':
            kids = []
            cur = nd
            while cur and cur.get('label') == 'ParamList':
                if cur.get('left'):
                    kids.append(cur['left'])
                cur = cur.get('right')
            if cur:
                kids.append(cur)
            return kids

        # Normal node: left then right
        kids = []
        if nd.get('left'):
            kids.append(nd['left'])
        if nd.get('right'):
            kids.append(nd['right'])
        return kids

    # ── recursive box builder ────────────────────────────────────────

    def _build(nd):
        """Build an ASCII box for *nd*.

        Returns ``(lines, width, center)`` where *center* is the
        column index of this node's label centre in the box.
        """
        if nd is None:
            return [], 0, 0

        s    = _lbl(nd)
        slen = len(s)
        kids = _children(nd)

        # ── leaf ─────────────────────────────────────────────────────
        if not kids:
            return [s], slen, slen // 2

        # ── recursively build every child ────────────────────────────
        boxes = [_build(k) for k in kids]   # [(lines, w, c), …]

        # ==============================================================
        #  SINGLE CHILD  –  use ``|`` connector
        # ==============================================================
        if len(boxes) == 1:
            cl, cw, cc = boxes[0]
            if slen >= cw:
                pc     = slen // 2
                cshift = max(0, pc - cc)
                w      = max(slen, cshift + cw)
                row0   = s
                row1   = ' ' * pc + '|'
                clines = [' ' * cshift + ln for ln in cl]
            else:
                pstart = max(0, cc - slen // 2)
                pc     = pstart + slen // 2
                w      = max(pstart + slen, cw)
                row0   = ' ' * pstart + s
                row1   = ' ' * cc + '|'
                clines = list(cl)
            return [r.rstrip() for r in [row0, row1] + clines], w, pc

        # ==============================================================
        #  MULTIPLE CHILDREN  –  ``/`` ``|`` ``\`` connectors
        # ==============================================================

        # -- lay children out side-by-side with GAP spacing --
        offsets = []
        x = 0
        for cl, cw, cc in boxes:
            offsets.append(x)
            x += cw + GAP

        # child centres in the combined coordinate system
        ccenters = [offsets[i] + boxes[i][2] for i in range(len(boxes))]

        # parent centre = midpoint between first and last child centres
        pcenter = (ccenters[0] + ccenters[-1]) // 2
        pstart  = pcenter - slen // 2

        # shift everything right if parent would start at a negative col
        shift = max(0, -pstart)
        if shift:
            pstart  += shift
            pcenter += shift
            offsets  = [o + shift for o in offsets]
            ccenters = [c + shift for c in ccenters]

        total_w = max(offsets[-1] + boxes[-1][1], pstart + slen)

        # -- row 0: parent label --
        row0 = ' ' * pstart + s

        # -- row 1: connector characters --
        n   = len(boxes)
        mid = n / 2.0           # float midpoint
        conn = [' '] * (total_w + 1)
        for i, cc in enumerate(ccenters):
            if n == 2:
                ch = '/' if i == 0 else '\\'
            elif i < mid - 0.5:
                ch = '/'
            elif i > mid - 0.5:
                ch = '\\'
            else:
                ch = '|'
            if 0 <= cc < len(conn):
                conn[cc] = ch
        row1 = ''.join(conn)

        # -- merge children rows side-by-side --
        max_h  = max(len(b[0]) for b in boxes)
        merged = []
        for ri in range(max_h):
            row = list(' ' * (total_w + 1))
            for i, (cl, cw, cc) in enumerate(boxes):
                off = offsets[i]
                if ri < len(cl):
                    line = cl[ri]
                    for j, ch in enumerate(line):
                        if off + j < len(row):
                            row[off + j] = ch
            merged.append(''.join(row))

        result = [row0, row1] + merged
        return [r.rstrip() for r in result], total_w, pcenter

    # ── entry point ──────────────────────────────────────────────────
    if not node:
        return ''
    lines, _, _ = _build(node)
    return '\n'.join(l.rstrip() for l in lines)


# =====================================================================
#  PHASE 3 -- Semantic Analysis (symbol table + annotated tree)
# =====================================================================
PHASE3_ROLE = "Semantic Analysis"
PHASE3_DESC = (
    "Performs meaning-level checks that go beyond grammar. Builds a "
    "Symbol Table recording every declared identifier together with "
    "its type, kind (variable / function / parameter), scope, and "
    "declaring line. Then walks the syntax tree a second time to "
    "produce a Semantic Tree -- a copy of the syntax tree where each "
    "node is annotated with resolved type information. Undeclared "
    "variable usage is reported as an error."
)

_STDLIB = {
    'printf', 'scanf', 'main', 'malloc', 'free', 'strlen', 'strcmp',
    'strcpy', 'strcat', 'memset', 'memcpy', 'fopen', 'fclose',
    'fprintf', 'fscanf', 'fgets', 'fputs', 'getchar', 'putchar',
    'puts', 'gets', 'atoi', 'atof', 'exit', 'abs', 'sizeof',
    'NULL', 'EOF', 'stdin', 'stdout', 'stderr', 'fgetc', 'getc',
    'fputc', 'putc', 'sscanf', 'sprintf', 'snprintf', 'assert',
    'rand', 'srand', 'time', 'clock', 'sleep', 'usleep',
    'pow', 'sqrt', 'sin', 'cos', 'tan', 'log', 'exp', 'ceil', 'floor',
    'calloc', 'realloc', 'qsort', 'bsearch', 'isalpha', 'isdigit',
    'toupper', 'tolower', 'swap',
    'DBL_MAX', 'DBL_MIN', 'FLT_MAX', 'FLT_MIN', 'INT_MAX', 'INT_MIN',
    'LONG_MAX', 'LONG_MIN', 'ULONG_MAX', 'CHAR_MAX', 'CHAR_MIN',
    'SIZE_MAX', 'RAND_MAX', 'true', 'false', 'TRUE', 'FALSE',
}


def _build_symtab(tokens):
    TYPE_KW = {'int', 'float', 'double', 'char', 'void', 'long', 'short', 'unsigned', 'signed'}
    tl = [(t['type'], t['value'], t.get('line', 0)) for t in tokens]
    declared = {}
    used = []
    i = 0
    while i < len(tl):
        tt, tv, tln = tl[i]
        if tt == 'KEYWORD' and tv in TYPE_KW:
            j = i + 1
            while j < len(tl) and tl[j][0] == 'KEYWORD' and tl[j][1] in TYPE_KW:
                j += 1
            tp = ' '.join(tl[k][1] for k in range(i, j))
            # Parse first identifier
            if j < len(tl) and tl[j][0] == 'ID':
                vn = tl[j][1]
                kind = 'function' if j + 1 < len(tl) and tl[j + 1][0] == 'LPAREN' else 'variable'
                declared[vn] = {'name': vn, 'type': tp, 'kind': kind, 'scope': 'global', 'line': tln}
                j += 1
                # Skip array brackets like [10]
                if j < len(tl) and tl[j][0] == 'LBRACK':
                    while j < len(tl) and tl[j][0] != 'RBRACK':
                        j += 1
                    if j < len(tl):
                        j += 1  # skip RBRACK
                # Skip initializer (= expr)
                if j < len(tl) and tl[j][0] == 'ASSIGN':
                    j += 1
                    # Skip until COMMA or SEMICOLON (respecting parens/braces)
                    depth = 0
                    while j < len(tl):
                        if tl[j][0] in ('LPAREN', 'LBRACE', 'LBRACK'):
                            depth += 1
                        elif tl[j][0] in ('RPAREN', 'RBRACE', 'RBRACK'):
                            depth -= 1
                        elif depth == 0 and tl[j][0] in ('COMMA', 'SEMICOLON'):
                            break
                        j += 1
                # Continue parsing comma-separated identifiers: int a, b, c;
                while j < len(tl) and tl[j][0] == 'COMMA':
                    j += 1  # skip COMMA
                    # Skip pointer stars
                    while j < len(tl) and tl[j][1] == '*':
                        j += 1
                    if j < len(tl) and tl[j][0] == 'ID':
                        vn2 = tl[j][1]
                        declared[vn2] = {'name': vn2, 'type': tp, 'kind': 'variable', 'scope': 'global', 'line': tl[j][2]}
                        j += 1
                        # Skip array brackets
                        if j < len(tl) and tl[j][0] == 'LBRACK':
                            while j < len(tl) and tl[j][0] != 'RBRACK':
                                j += 1
                            if j < len(tl):
                                j += 1
                        # Skip initializer
                        if j < len(tl) and tl[j][0] == 'ASSIGN':
                            j += 1
                            depth = 0
                            while j < len(tl):
                                if tl[j][0] in ('LPAREN', 'LBRACE', 'LBRACK'):
                                    depth += 1
                                elif tl[j][0] in ('RPAREN', 'RBRACE', 'RBRACK'):
                                    depth -= 1
                                elif depth == 0 and tl[j][0] in ('COMMA', 'SEMICOLON'):
                                    break
                                j += 1
                    else:
                        break
                i = j
                continue
        if tt == 'ID' and tv not in TYPE_KW:
            is_decl = False
            if i > 0:
                prev = tl[i - 1]
                if prev[0] == 'KEYWORD' and prev[1] in TYPE_KW:
                    is_decl = True
                elif prev[0] == 'COMMA' and tv in declared:
                    is_decl = True  # part of comma-separated decl already handled
            if not is_decl:
                used.append((tv, tln))
        i += 1
    errors = []
    for vn, ln in used:
        if vn not in declared and vn not in _STDLIB:
            errors.append({
                'message': f"Undeclared variable '{vn}' used at line {ln}",
                'line': ln, 'variable': vn,
            })
    return list(declared.values()), errors


def _annotate_tree(node, symtab_map):
    """Deep-copy the syntax tree, annotating each node with a 'type_info' field."""
    if node is None:
        return None
    out = dict(node)  # shallow copy
    lbl = node.get('label', '')
    val = node.get('value', '')

    if lbl == 'Id' and val in symtab_map:
        out['type_info'] = symtab_map[val]['type']
    elif lbl == 'Num':
        out['type_info'] = 'double' if '.' in val else 'int'
    elif lbl == 'Str':
        out['type_info'] = 'char*'
    elif lbl == 'Char':
        out['type_info'] = 'char'
    elif lbl == 'Decl' and val:
        parts = val.strip().split()
        if len(parts) >= 2 and parts[-1] in symtab_map:
            out['type_info'] = symtab_map[parts[-1]]['type']
    elif lbl == 'FunctionDef' and val:
        parts = val.strip().split()
        fname = parts[-1] if parts else ''
        if fname in symtab_map:
            out['type_info'] = f"returns {symtab_map[fname]['type']}"
    elif lbl == 'Call' and val in symtab_map:
        out['type_info'] = symtab_map[val]['type']
    elif lbl in ('BinOp', 'Assign'):
        out['type_info'] = 'int'
    elif lbl == 'ReturnStmt':
        out['type_info'] = 'int'

    if 'left' in node:
        out['left'] = _annotate_tree(node.get('left'), symtab_map)
    if 'right' in node:
        out['right'] = _annotate_tree(node.get('right'), symtab_map)
    return out


def phase_semantic(tokens, syntax_tree):
    sym_list, errors = _build_symtab(tokens)
    sym_map = {s['name']: s for s in sym_list}
    semantic_tree = _annotate_tree(syntax_tree, sym_map)
    return {'symbol_table': sym_list, 'semantic_tree': semantic_tree, 'errors': errors}


# =====================================================================
#  PHASE 4 -- Intermediate Code Generation (Three Address Code)
# =====================================================================
PHASE4_ROLE = "Intermediate Code Generation (ICG)"
PHASE4_DESC = (
    "Walks the syntax tree and emits Three Address Code (TAC) -- a "
    "linear, platform-independent intermediate representation where "
    "each instruction has at most three operands. Temporary variables "
    "(t1, t2, ...) and labels (L1, L2, ...) are introduced for complex "
    "expressions and control flow."
)


class _TACGen:
    """Generate TAC from the token stream."""

    TYPE_KW = {
        'int', 'float', 'double', 'char', 'void', 'long', 'short',
        'unsigned', 'signed', 'const', 'static', 'extern', 'struct',
    }

    def __init__(self, tokens):
        self.toks = [(t['type'], t['value']) for t in tokens]
        self.pos = 0
        self.tac = []
        self.tc = 0
        self.lc = 0

    def _nt(self):
        self.tc += 1
        return f't{self.tc}'

    def _nl(self):
        self.lc += 1
        return f'L{self.lc}'

    def _cur(self):
        return self.toks[self.pos] if self.pos < len(self.toks) else ('EOF', '')

    def _eat(self):
        t = self._cur()
        self.pos += 1
        return t

    def _match(self, k, v=None):
        t = self._cur()
        return t[0] == k and (v is None or t[1] == v)

    def generate(self):
        while self._cur()[0] != 'EOF':
            self._top()
        return self.tac

    def _top(self):
        if self._cur()[0] == 'KEYWORD' and self._cur()[1] in self.TYPE_KW:
            self._decl_or_func()
        else:
            self._eat()

    def _decl_or_func(self):
        while self._cur()[0] == 'KEYWORD' and self._cur()[1] in self.TYPE_KW:
            self._eat()
        while self._cur()[1] == '*':
            self._eat()
        if not self._match('ID'):
            return
        name = self._eat()[1]
        if self._match('LPAREN'):
            self._func(name)
        else:
            self._vdecl(name)

    def _vdecl(self, name):
        if self._cur()[1] == '=':
            self._eat()
            val = self._collect_expr()
            self.tac.append(f'{name} = {val}')
        else:
            self.tac.append(f'DECL {name}')
        # Handle comma-separated declarations: int a, b, c;
        while self._match('COMMA'):
            self._eat()  # eat COMMA
            while self._cur()[1] == '*':
                self._eat()  # pointer stars
            if self._match('ID'):
                vname = self._eat()[1]
                if self._match('LBRACK'):
                    self._eat()
                    if not self._match('RBRACK'):
                        self._eat()
                    if self._match('RBRACK'):
                        self._eat()
                if self._cur()[1] == '=':
                    self._eat()
                    val = self._collect_expr()
                    self.tac.append(f'{vname} = {val}')
                else:
                    self.tac.append(f'DECL {vname}')
            else:
                break
        if self._match('SEMICOLON'):
            self._eat()

    def _func(self, name):
        self.tac.append(f'FUNC_BEGIN {name}')
        self._eat()  # (
        params = []
        while self._cur()[0] != 'EOF' and self._cur()[0] != 'RPAREN':
            if self._cur()[0] == 'KEYWORD' and self._cur()[1] in self.TYPE_KW:
                while self._cur()[0] == 'KEYWORD' and self._cur()[1] in self.TYPE_KW:
                    self._eat()
                while self._cur()[1] == '*':
                    self._eat()
                if self._match('ID'):
                    pname = self._eat()[1]
                    params.append(pname)
                    if self._match('LBRACK'):
                        self._eat()
                        if not self._match('RBRACK'):
                            self._eat()
                        if self._match('RBRACK'):
                            self._eat()
            elif self._match('COMMA'):
                self._eat()
            else:
                self._eat()
        if self._match('RPAREN'):
            self._eat()
        for p in params:
            self.tac.append(f'PARAM {p}')
        if self._match('LBRACE'):
            self._block()
        self.tac.append(f'FUNC_END {name}')

    def _block(self):
        self._eat()
        d = 1
        while d > 0 and self._cur()[0] != 'EOF':
            if self._cur()[0] == 'LBRACE':
                d += 1
                self._eat()
            elif self._cur()[0] == 'RBRACE':
                d -= 1
                self._eat()
            else:
                self._stmt()

    def _stmt(self):
        c = self._cur()
        if c[0] == 'KEYWORD' and c[1] == 'return':
            self._eat()
            if self._match('SEMICOLON'):
                self.tac.append('RETURN')
                self._eat()
            else:
                v = self._collect_expr()
                self.tac.append(f'RETURN {v}')
                if self._match('SEMICOLON'):
                    self._eat()
            return
        if c[0] == 'KEYWORD' and c[1] == 'if':
            self._if_stmt()
            return
        if c[0] == 'KEYWORD' and c[1] == 'while':
            self._while_stmt()
            return
        if c[0] == 'KEYWORD' and c[1] == 'for':
            self._for_stmt()
            return
        if c[0] == 'KEYWORD' and c[1] == 'do':
            self._do_while_stmt()
            return
        if c[0] == 'KEYWORD' and c[1] == 'switch':
            self._switch_stmt()
            return
        if c[0] == 'KEYWORD' and c[1] in ('break', 'continue'):
            self._eat()
            if self._match('SEMICOLON'):
                self._eat()
            return
        if c[0] == 'KEYWORD' and c[1] in ('case', 'default'):
            # handled by _switch_stmt; skip if encountered outside
            self._eat()
            return
        if c[0] == 'KEYWORD' and c[1] in self.TYPE_KW:
            while self._cur()[0] == 'KEYWORD' and self._cur()[1] in self.TYPE_KW:
                self._eat()
            while self._cur()[1] == '*':
                self._eat()
            if self._match('ID'):
                nm = self._eat()[1]
                if self._match('LBRACK'):
                    self._eat()
                    if not self._match('RBRACK'):
                        self._eat()
                    if self._match('RBRACK'):
                        self._eat()
                if self._cur()[1] == '=':
                    self._eat()
                    v = self._collect_expr()
                    self.tac.append(f'{nm} = {v}')
                else:
                    self.tac.append(f'DECL {nm}')
                # Handle comma-separated declarations in local scope
                while self._match('COMMA'):
                    self._eat()  # eat COMMA
                    while self._cur()[1] == '*':
                        self._eat()
                    if self._match('ID'):
                        nm2 = self._eat()[1]
                        if self._match('LBRACK'):
                            self._eat()
                            if not self._match('RBRACK'):
                                self._eat()
                            if self._match('RBRACK'):
                                self._eat()
                        if self._cur()[1] == '=':
                            self._eat()
                            v2 = self._collect_expr()
                            self.tac.append(f'{nm2} = {v2}')
                        else:
                            self.tac.append(f'DECL {nm2}')
                    else:
                        break
            if self._match('SEMICOLON'):
                self._eat()
            return
        if c[0] == 'ID':
            nm = self._eat()[1]
            if self._match('LBRACK'):
                self._eat()  # [
                idx = self._cuntil('RBRACK')
                self._eat()  # ]
                if self._cur()[1] == '=':
                    self._eat()
                    v = self._collect_expr()
                    self.tac.append(f'{nm} [ {idx} ] = {v}')
                elif self._cur()[1] in ('++', '--'):
                    op = self._eat()[1]
                    t = self._nt()
                    self.tac.append(f'{t} = {nm} [ {idx} ] {op[0]} 1')
                    self.tac.append(f'{nm} [ {idx} ] = {t}')
            elif self._cur()[1] == '=':
                self._eat()
                v = self._collect_expr()
                self.tac.append(f'{nm} = {v}')
            elif self._match('LPAREN'):
                args = self._cargs()
                self.tac.append(f'CALL {nm}({args})')
            elif self._cur()[1] in ('++', '--'):
                op = self._eat()[1]
                t = self._nt()
                self.tac.append(f'{t} = {nm} {op[0]} 1')
                self.tac.append(f'{nm} = {t}')
            if self._match('SEMICOLON'):
                self._eat()
            return
        self._eat()

    def _if_stmt(self):
        self._eat()
        self._eat()  # (
        cond = self._cuntil('RPAREN')
        self._eat()  # )
        le = self._nl()
        lend = self._nl()
        self.tac.append(f'IF_FALSE {cond} GOTO {le}')
        if self._match('LBRACE'):
            self._block()
        else:
            self._stmt()
        if self._match('KEYWORD', 'else'):
            self.tac.append(f'GOTO {lend}')
            self.tac.append(f'{le}:')
            self._eat()
            if self._match('LBRACE'):
                self._block()
            else:
                self._stmt()
            self.tac.append(f'{lend}:')
        else:
            self.tac.append(f'{le}:')

    def _while_stmt(self):
        self._eat()
        self._eat()  # (
        ls = self._nl()
        le = self._nl()
        self.tac.append(f'{ls}:')
        cond = self._cuntil('RPAREN')
        self._eat()  # )
        self.tac.append(f'IF_FALSE {cond} GOTO {le}')
        if self._match('LBRACE'):
            self._block()
        else:
            self._stmt()
        self.tac.append(f'GOTO {ls}')
        self.tac.append(f'{le}:')

    def _for_stmt(self):
        self._eat()
        self._eat()  # (
        init = self._cuntil('SEMICOLON')
        self._eat()  # ;
        if init.strip():
            self.tac.append(init.strip())
        ls = self._nl()
        le = self._nl()
        self.tac.append(f'{ls}:')
        cond = self._cuntil('SEMICOLON')
        self._eat()  # ;
        if cond.strip():
            self.tac.append(f'IF_FALSE {cond.strip()} GOTO {le}')
        upd = self._cuntil('RPAREN')
        self._eat()  # )
        if self._match('LBRACE'):
            self._block()
        else:
            self._stmt()
        if upd.strip():
            self.tac.append(upd.strip())
        self.tac.append(f'GOTO {ls}')
        self.tac.append(f'{le}:')

    def _do_while_stmt(self):
        self._eat()  # do
        ls = self._nl()
        le = self._nl()
        self.tac.append(f'{ls}:')
        if self._match('LBRACE'):
            self._block()
        else:
            self._stmt()
        if self._match('KEYWORD', 'while'):
            self._eat()
        self._eat()  # (
        cond = self._cuntil('RPAREN')
        self._eat()  # )
        self.tac.append(f'IF_FALSE {cond} GOTO {le}')
        self.tac.append(f'GOTO {ls}')
        self.tac.append(f'{le}:')
        if self._match('SEMICOLON'):
            self._eat()

    def _switch_stmt(self):
        self._eat()  # switch
        self._eat()  # (
        switch_expr = self._cuntil('RPAREN')
        self._eat()  # )
        # save the switch value to a temp
        tv = self._nt()
        self.tac.append(f'{tv} = {switch_expr}')
        self._eat()  # {

        # collect case/default labels before emitting body
        # We'll generate: compare, conditional jumps, then case bodies
        lend = self._nl()  # label for break target (end of switch)

        # We need to parse case/default inside the braces and generate TAC
        # Strategy: generate IF checks at the top, then bodies with labels
        cases = []  # list of (value_str, label)
        default_label = None
        # First, gather all case values and assign labels
        # But we can't peek ahead easily. Instead, do single-pass:
        # emit code as we encounter case/default,
        # replace 'break' with GOTO lend

        # Single-pass approach:
        # For each case, emit label then body.  Before the switch body,
        # we emit a jump table.

        # Actually, let's collect cases in one pass through the braces:
        # We'll save our position, scan ahead for case/default values,
        # then rewind and generate code.

        # Simpler approach: Convert switch to if-else chain.
        # Parse the block manually, tracking case values.

        # Parse all cases by scanning the tokens inside { ... }
        # each case becomes: if (tv == value) goto case_label
        case_bodies = []  # (value|None, body_tac_list)
        depth = 1
        saved_tac = self.tac
        while depth > 0 and self._cur()[0] != 'EOF':
            c = self._cur()
            if c[0] == 'LBRACE':
                depth += 1
                self._eat()
            elif c[0] == 'RBRACE':
                depth -= 1
                if depth == 0:
                    self._eat()
                    break
                self._eat()
            elif c[0] == 'KEYWORD' and c[1] == 'case':
                self._eat()  # case
                val = self._cuntil('COLON')
                self._eat()  # :
                cl = self._nl()
                body_tac = []
                self.tac = body_tac
                # parse statements until next case/default/}
                while (self._cur()[0] != 'EOF'
                       and not (self._cur()[0] == 'KEYWORD' and self._cur()[1] == 'case')
                       and not (self._cur()[0] == 'KEYWORD' and self._cur()[1] == 'default')
                       and not (self._cur()[0] == 'RBRACE' and depth == 1)):
                    if self._cur()[0] == 'KEYWORD' and self._cur()[1] == 'break':
                        self._eat()
                        if self._match('SEMICOLON'):
                            self._eat()
                        body_tac.append(f'GOTO {lend}')
                        break
                    self._stmt()
                case_bodies.append((val.strip(), cl, body_tac))
            elif c[0] == 'KEYWORD' and c[1] == 'default':
                self._eat()  # default
                if self._match('COLON'):
                    self._eat()  # :
                dl = self._nl()
                default_label = dl
                body_tac = []
                self.tac = body_tac
                while (self._cur()[0] != 'EOF'
                       and not (self._cur()[0] == 'KEYWORD' and self._cur()[1] == 'case')
                       and not (self._cur()[0] == 'RBRACE' and depth == 1)):
                    if self._cur()[0] == 'KEYWORD' and self._cur()[1] == 'break':
                        self._eat()
                        if self._match('SEMICOLON'):
                            self._eat()
                        body_tac.append(f'GOTO {lend}')
                        break
                    self._stmt()
                case_bodies.append((None, dl, body_tac))
            else:
                self._eat()

        # eat closing } if we haven't yet
        self.tac = saved_tac

        # Emit jump table: if tv == val GOTO label
        for val, cl, _ in case_bodies:
            if val is not None:
                self.tac.append(f'IF_FALSE {tv} == {val} GOTO {cl}_skip')
                self.tac.append(f'GOTO {cl}')
                self.tac.append(f'{cl}_skip:')
        if default_label:
            self.tac.append(f'GOTO {default_label}')
        else:
            self.tac.append(f'GOTO {lend}')

        # Emit case bodies
        for val, cl, body in case_bodies:
            self.tac.append(f'{cl}:')
            self.tac.extend(body)

        self.tac.append(f'{lend}:')

    def _collect_expr(self):
        parts = []
        while self._cur()[0] != 'EOF' and not self._match('SEMICOLON'):
            t = self._cur()
            if t[0] == 'LPAREN':
                # Function call: identifier followed by (
                if parts:
                    last = parts[-1] if parts else ''
                    if isinstance(last, str) and last not in ('+', '-', '*', '/', '%', '=', '<', '>', '!', '&', '|', '(', '==', '!=', '<=', '>=', '&&', '||'):
                        fn = parts.pop()
                        args = self._cargs()
                        tmp = self._nt()
                        self.tac.append(f'{tmp} = CALL {fn}({args})')
                        parts.append(tmp)
                        continue
                # Parenthesized subexpression: collect inner tokens, linearize to temp
                self._eat()  # (
                inner_parts = []
                depth = 1
                while depth > 0 and self._cur()[0] != 'EOF':
                    if self._cur()[0] == 'LPAREN':
                        depth += 1
                    elif self._cur()[0] == 'RPAREN':
                        depth -= 1
                        if depth == 0:
                            self._eat()  # )
                            break
                    # Handle array subscript inside parens
                    if self._cur()[0] == 'LBRACK' and inner_parts:
                        last_inner = inner_parts[-1] if inner_parts else ''
                        if isinstance(last_inner, str) and re.match(r'^[a-zA-Z_]\w*$', str(last_inner)):
                            arr_name = inner_parts.pop()
                            self._eat()  # [
                            idx_parts = []
                            bdepth = 1
                            while bdepth > 0 and self._cur()[0] != 'EOF':
                                if self._cur()[0] == 'LBRACK':
                                    bdepth += 1
                                elif self._cur()[0] == 'RBRACK':
                                    bdepth -= 1
                                    if bdepth == 0:
                                        self._eat()  # ]
                                        break
                                idx_parts.append(self._cur()[1])
                                self._eat()
                            idx_expr = ' '.join(idx_parts)
                            inner_parts.append(f'{arr_name} [ {idx_expr} ]')
                            continue
                    inner_parts.append(self._cur()[1])
                    self._eat()
                if len(inner_parts) >= 3:
                    result = self._linearize(inner_parts)
                    if not re.match(r'^t\d+$', result):
                        tmp = self._nt()
                        self.tac.append(f'{tmp} = {result}')
                        parts.append(tmp)
                    else:
                        parts.append(result)
                elif inner_parts:
                    parts.append(' '.join(str(p) for p in inner_parts))
                continue
            # Handle array subscript: arr[index] as a single operand
            if t[0] == 'LBRACK' and parts:
                last = parts[-1] if parts else ''
                if isinstance(last, str) and re.match(r'^[a-zA-Z_]\w*$', str(last)):
                    arr_name = parts.pop()
                    self._eat()  # [
                    idx_parts = []
                    depth = 1
                    while depth > 0 and self._cur()[0] != 'EOF':
                        if self._cur()[0] == 'LBRACK':
                            depth += 1
                        elif self._cur()[0] == 'RBRACK':
                            depth -= 1
                            if depth == 0:
                                self._eat()  # ]
                                break
                        idx_parts.append(self._cur()[1])
                        self._eat()
                    idx_expr = ' '.join(idx_parts)
                    parts.append(f'{arr_name} [ {idx_expr} ]')
                    continue
            parts.append(t[1])
            self._eat()
        if len(parts) >= 3:
            result = self._linearize(parts)
            # Create a temp for compound non-operator expressions (e.g. arr[i])
            # so the optimizer can apply copy propagation
            if not re.match(r'^t\d+$', result) and ' ' in result:
                t = self._nt()
                self.tac.append(f'{t} = {result}')
                return t
            return result
        return ' '.join(str(p) for p in parts)

    def _linearize(self, parts):
        # Process operators by precedence (highest first)
        for op_set in [{'*', '/', '%'}, {'+', '-'},
                       {'<', '>', '<=', '>=', '==', '!='},
                       {'&&', '||'}]:
            parts = self._linearize_pass(parts, op_set)
        if len(parts) == 1:
            return str(parts[0])
        return ' '.join(str(p) for p in parts)

    def _linearize_pass(self, parts, ops):
        if len(parts) < 3:
            return parts
        new_parts = []
        i = 0
        while i < len(parts):
            if i > 0 and i < len(parts) - 1 and str(parts[i]) in ops:
                left = new_parts.pop() if new_parts else parts[i - 1]
                right = parts[i + 1]
                t = self._nt()
                self.tac.append(f'{t} = {left} {parts[i]} {right}')
                new_parts.append(t)
                i += 2
            else:
                new_parts.append(parts[i])
                i += 1
        return new_parts

    def _cargs(self):
        self._eat()  # (
        d = 1
        ps = []
        while d > 0 and self._cur()[0] != 'EOF':
            if self._cur()[0] == 'LPAREN':
                d += 1
            elif self._cur()[0] == 'RPAREN':
                d -= 1
                if d == 0:
                    self._eat()
                    break
            ps.append(self._cur()[1])
            self._eat()
        return ' '.join(ps)

    def _cuntil(self, stop):
        ps = []
        while self._cur()[0] != 'EOF' and self._cur()[0] != stop:
            ps.append(self._cur()[1])
            self._eat()
        return ' '.join(ps)


def phase_intermediate(tokens):
    try:
        g = _TACGen(tokens)
        tac = g.generate()
        return {'ir': tac, 'errors': []}
    except Exception as ex:
        return {'ir': [], 'errors': [{'message': f'IR error: {ex}'}]}


# =====================================================================
#  PHASE 5 -- Code Optimization
# =====================================================================
PHASE5_ROLE = "Code Optimization"
PHASE5_DESC = (
    "Applies machine-independent optimizations to the TAC:\n"
    "- Constant Folding -- evaluates compile-time constant expressions "
    "(e.g. 3 + 4 -> 7).\n"
    "- Constant Propagation -- replaces variables whose values are "
    "known constants.\n"
    "- Algebraic Simplification -- removes identity operations "
    "(x + 0 -> x, x * 1 -> x, x * 0 -> 0, x - 0 -> x).\n"
    "- Strength Reduction -- replaces expensive ops with cheaper ones "
    "(x * 2 -> x << 1, x * 4 -> x << 2).\n"
    "- Copy Propagation -- inlines temporary variables that are used "
    "only once (t1 = a+b; sum = t1 -> sum = a+b).\n"
    "- Dead Code Elimination -- removes temporary variable assignments "
    "that are no longer referenced after other optimizations.\n"
    "The original TAC and the optimized TAC are shown side by side "
    "so you can see exactly what changed."
)

_ASSIGN_RE = re.compile(r'^(\w+)\s*=\s*(.+)$')
_BINOP_RE = re.compile(r'^(\S+)\s*([+\-*/%])\s*(\S+)$')
_INC_RE = re.compile(r'^(\w+)\s*(\+\+|--)$')
_POWERS_OF_2 = {2: 1, 4: 2, 8: 3, 16: 4, 32: 5, 64: 6, 128: 7, 256: 8}


def _try_num(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return None


def _find_unsafe_vars(tac_lines):
    """Find variables that must NOT be constant-propagated.

    A variable is unsafe if it is:
    * modified (assigned or incremented) inside any loop body, OR
    * modified by a CALL with a reference argument ``&var``.

    Loop detection: a backward GOTO (``GOTO Lx`` where ``Lx:`` appeared
    earlier) defines a loop from the label to the GOTO.
    """
    # Step 1: map label -> position
    label_pos = {}
    for idx, raw in enumerate(tac_lines):
        g = raw.strip()
        if g.endswith(':') and not g.startswith(';'):
            label_pos[g[:-1]] = idx

    # Step 2: backward GOTOs define loop ranges
    loop_ranges = []
    for idx, raw in enumerate(tac_lines):
        g = raw.strip()
        if g.startswith('GOTO '):
            target = g[5:].strip()
            if target in label_pos and label_pos[target] <= idx:
                loop_ranges.append((label_pos[target], idx))

    # Step 3: collect variables modified in any loop range
    unsafe = set()
    for start, end in loop_ranges:
        for i in range(start, end + 1):
            g = tac_lines[i].strip()
            am = _ASSIGN_RE.match(g)
            if am:
                unsafe.add(am.group(1))
            im = _INC_RE.match(g)
            if im:
                unsafe.add(im.group(1))
            if g.startswith('CALL'):
                for ref in re.findall(r'&\s*(\w+)', g):
                    unsafe.add(ref)

    # Step 4: variables modified through CALL scanf(&var) anywhere
    for raw in tac_lines:
        g = raw.strip()
        if g.startswith('CALL'):
            for ref in re.findall(r'&\s*(\w+)', g):
                unsafe.add(ref)

    return unsafe


def phase_optimization(tac_lines):
    optimized = []
    changes = []
    consts = {}  # variable -> known constant value string

    unsafe_vars = _find_unsafe_vars(tac_lines)

    for raw_line in tac_lines:
        line = raw_line.strip()
        if not line:
            optimized.append(raw_line)
            continue

        # -- Increment / decrement: ``i ++`` or ``i --`` --
        im = _INC_RE.match(line)
        if im:
            consts.pop(im.group(1), None)
            optimized.append(raw_line)
            continue

        # -- Labels: control-flow merge points --
        if line.endswith(':') and not line.startswith(';'):
            for v in list(consts):
                if v in unsafe_vars:
                    consts.pop(v, None)
            optimized.append(raw_line)
            continue

        # -- FUNC boundaries: clear all constants --
        if line.startswith('FUNC_BEGIN') or line.startswith('FUNC_END'):
            consts.clear()
            optimized.append(raw_line)
            continue

        # -- CALL: invalidates variables passed by reference --
        if line.startswith('CALL'):
            for ref in re.findall(r'&\s*(\w+)', line):
                consts.pop(ref, None)
            optimized.append(raw_line)
            continue

        # -- other control flow: copy as-is --
        if (line.startswith('GOTO ') or line.startswith('IF_FALSE')
                or line.startswith('RETURN') or line.startswith('DECL ')
                or line.startswith('PARAM ')):
            optimized.append(raw_line)
            continue

        m = _ASSIGN_RE.match(line)
        if not m:
            optimized.append(raw_line)
            continue

        dest, rhs = m.group(1), m.group(2).strip()

        # --- constant propagation on rhs: only substitute safe vars ---
        prop_rhs = rhs
        changed_by_prop = False
        for var, val in list(consts.items()):
            if var in unsafe_vars:
                continue
            new = re.sub(r'\b' + re.escape(var) + r'\b', val, prop_rhs)
            if new != prop_rhs:
                prop_rhs = new
                changed_by_prop = True

        # --- try binary operator ---
        bm = _BINOP_RE.match(prop_rhs)
        if bm:
            left_s, op, right_s = bm.group(1), bm.group(2), bm.group(3)
            left_v, right_v = _try_num(left_s), _try_num(right_s)

            # 1) constant folding -- both sides are numbers
            if left_v is not None and right_v is not None:
                result = None
                try:
                    if op == '+':
                        result = left_v + right_v
                    elif op == '-':
                        result = left_v - right_v
                    elif op == '*':
                        result = left_v * right_v
                    elif op == '/' and right_v != 0:
                        result = left_v / right_v
                    elif op == '%' and right_v != 0:
                        result = left_v % right_v
                except Exception:
                    pass
                if result is not None:
                    if isinstance(result, float) and result == int(result):
                        result = int(result)
                    new_line = f'{dest} = {result}'
                    optimized.append(new_line)
                    if dest not in unsafe_vars:
                        consts[dest] = str(result)
                    changes.append({'original': raw_line, 'optimized': new_line, 'rule': 'Constant Folding'})
                    continue

            # 2) algebraic simplification -- identity operations
            simplified = None
            rule = None
            if op == '+' and right_v == 0:
                simplified, rule = left_s, 'Algebraic Simplification: x+0 → x'
            elif op == '+' and left_v == 0:
                simplified, rule = right_s, 'Algebraic Simplification: 0+x → x'
            elif op == '-' and right_v == 0:
                simplified, rule = left_s, 'Algebraic Simplification: x-0 → x'
            elif op == '-' and left_s == right_s:
                simplified, rule = '0', 'Algebraic Simplification: x-x → 0'
            elif op == '*' and right_v == 1:
                simplified, rule = left_s, 'Algebraic Simplification: x*1 → x'
            elif op == '*' and left_v == 1:
                simplified, rule = right_s, 'Algebraic Simplification: 1*x → x'
            elif op == '*' and (right_v == 0 or left_v == 0):
                simplified, rule = '0', 'Algebraic Simplification: x*0 → 0'
            elif op == '/' and right_v == 1:
                simplified, rule = left_s, 'Algebraic Simplification: x/1 → x'
            elif op == '/' and left_s == right_s and left_s != '0':
                simplified, rule = '1', 'Algebraic Simplification: x/x → 1'

            if simplified is not None:
                new_line = f'{dest} = {simplified}'
                optimized.append(new_line)
                sv = _try_num(simplified)
                if sv is not None and dest not in unsafe_vars:
                    consts[dest] = simplified
                else:
                    consts.pop(dest, None)
                changes.append({'original': raw_line, 'optimized': new_line, 'rule': rule})
                continue

            # 3) strength reduction -- x * 2^n -> x << n
            if op == '*' and right_v is not None and isinstance(right_v, int) and int(right_v) in _POWERS_OF_2:
                shift = _POWERS_OF_2[int(right_v)]
                new_line = f'{dest} = {left_s} << {shift}'
                optimized.append(new_line)
                consts.pop(dest, None)
                changes.append({'original': raw_line, 'optimized': new_line, 'rule': f'Strength Reduction: *{int(right_v)} → <<{shift}'})
                continue

        # --- propagation produced a change (non-binary) ---
        if changed_by_prop:
            new_line = f'{dest} = {prop_rhs}'
            optimized.append(new_line)
            v = _try_num(prop_rhs)
            if v is not None and dest not in unsafe_vars:
                consts[dest] = prop_rhs
            else:
                consts.pop(dest, None)
            changes.append({'original': raw_line, 'optimized': new_line, 'rule': 'Constant Propagation'})
            continue

        # --- record simple constant assignments (only for safe vars) ---
        v = _try_num(rhs)
        if v is not None and dest not in unsafe_vars:
            consts[dest] = rhs
        else:
            consts.pop(dest, None)

        optimized.append(raw_line)

    # --- second pass: copy propagation + dead code elimination ---
    optimized, cp_changes = _copy_prop_dce(optimized)
    changes.extend(cp_changes)

    return {'optimized_ir': optimized, 'changes': changes, 'errors': []}


# -- Copy Propagation + Dead Code Elimination helper -------------------
_TEMP_NAME_RE = re.compile(r'^t\d+$')


def _copy_prop_dce(tac_lines):
    """Inline single-use compiler temps and remove dead temp assignments.

    Copy Propagation:  ``t1 = expr;  var = t1``  -->  ``var = expr``
    Dead Code Elimination: remove ``tN = …`` when tN is never referenced.
    """
    changes = []

    # 1. collect temp definitions  tN = <rhs>
    temp_defs = {}                      # name -> (index, rhs_string)
    for idx, raw in enumerate(tac_lines):
        m = _ASSIGN_RE.match(raw.strip())
        if m and _TEMP_NAME_RE.match(m.group(1)):
            temp_defs[m.group(1)] = (idx, m.group(2).strip())
    if not temp_defs:
        return tac_lines, changes

    # 2. count uses of each temp (excluding its definition line)
    def _uses(name, def_idx):
        pat = re.compile(r'\b' + re.escape(name) + r'\b')
        return [(i, tac_lines[i]) for i in range(len(tac_lines))
                if i != def_idx and pat.search(tac_lines[i])]

    result = list(tac_lines)
    dead = set()

    for tname, (def_idx, rhs) in temp_defs.items():
        uses = _uses(tname, def_idx)

        # --- 0 uses: pure dead code ---
        if len(uses) == 0:
            dead.add(def_idx)
            changes.append({'original': tac_lines[def_idx].strip(),
                            'optimized': '(removed)',
                            'rule': 'Dead Code Elimination'})
            continue

        # --- exactly 1 use that is  var = tN ---
        if len(uses) != 1:
            continue
        use_idx, use_raw = uses[0]
        um = _ASSIGN_RE.match(use_raw.strip())
        if not um or um.group(2).strip() != tname:
            continue                        # used inside a bigger expression

        # safety: ensure no RHS variable is modified between def and use
        rhs_ids = set(re.findall(r'\b([a-zA-Z_]\w*)\b', rhs)) - {'CALL'}
        safe = True
        for i in range(def_idx + 1, use_idx):
            g = tac_lines[i].strip()
            am = _ASSIGN_RE.match(g)
            if am and am.group(1) in rhs_ids:
                safe = False; break
            im = _INC_RE.match(g)
            if im and im.group(1) in rhs_ids:
                safe = False; break
            if g.startswith('CALL'):
                for ref in re.findall(r'&\s*(\w+)', g):
                    if ref in rhs_ids:
                        safe = False; break
                if not safe:
                    break
        if not safe:
            continue

        # apply copy propagation
        dest = um.group(1)
        new_line = f'{dest} = {rhs}'
        changes.append({'original': use_raw.strip(),
                        'optimized': new_line,
                        'rule': 'Copy Propagation'})
        result[use_idx] = new_line
        dead.add(def_idx)
        changes.append({'original': tac_lines[def_idx].strip(),
                        'optimized': '(removed)',
                        'rule': 'Dead Code Elimination'})

    final = [result[i] for i in range(len(result)) if i not in dead]
    return final, changes


# =====================================================================
#  PHASE 6 -- Code Generation (Pseudo Assembly)
# =====================================================================
PHASE6_ROLE = "Code Generation"
PHASE6_DESC = (
    "Translates the optimized TAC into pseudo assembly instructions "
    "for a simple register-based target architecture. Uses registers "
    "AX, BX, CX, DX, SP, BP. Emits MOV, ADD, SUB, MUL, DIV, SHL, "
    "CMP, JMP, JE, JNE, PUSH, POP, CALL, RET instructions."
)


def phase_codegen(tac_lines):
    asm = []
    for raw in tac_lines:
        line = raw.strip()
        if not line:
            continue
        if line.endswith(':'):
            asm.append(line)
            continue
        if line.startswith('FUNC_BEGIN'):
            nm = line.split(' ', 1)[1] if ' ' in line else ''
            asm += [f'; --- function {nm} ---', f'{nm}:', '    PUSH BP', '    MOV BP, SP']
            continue
        if line.startswith('FUNC_END'):
            asm += ['    POP BP', '    RET']
            continue
        if line.startswith('RETURN'):
            val = line[6:].strip()
            if val:
                asm.append(f'    MOV AX, {val}')
            asm += ['    POP BP', '    RET']
            continue
        if line.startswith('GOTO '):
            asm.append(f'    JMP {line[5:].strip()}')
            continue
        if line.startswith('IF_FALSE'):
            parts = line.split('GOTO')
            cond = parts[0].replace('IF_FALSE', '').strip()
            lbl = parts[1].strip() if len(parts) > 1 else '?'
            asm += [f'    CMP {cond}, 0', f'    JE {lbl}']
            continue
        if line.startswith('DECL'):
            var = line[4:].strip()
            asm += [f'    ; declare {var}', f'    SUB SP, 4  ; alloc {var}']
            continue
        if line.startswith('PARAM'):
            var = line[5:].strip()
            asm.append(f'    ; param {var}')
            continue

        cm = re.match(r'CALL\s+(\w+)\((.*)?\)', line)
        if cm:
            fn, ar = cm.group(1), cm.group(2) or ''
            if ar:
                for a in reversed(ar.split(',')):
                    asm.append(f'    PUSH {a.strip()}')
            asm.append(f'    CALL {fn}')
            continue
        tcm = re.match(r'(\w+)\s*=\s*CALL\s+(\w+)\((.*)?\)', line)
        if tcm:
            d, fn, ar = tcm.group(1), tcm.group(2), tcm.group(3) or ''
            if ar:
                for a in reversed(ar.split(',')):
                    asm.append(f'    PUSH {a.strip()}')
            asm += [f'    CALL {fn}', f'    MOV {d}, AX']
            continue

        # dest = left OP right (including <<)
        aop = re.match(r'(\w+)\s*=\s*(\S+)\s*(<<|>>|[+\-*/%<>=!&|]+)\s*(\S+)', line)
        if aop:
            d, l, op, r = aop.groups()
            asm.append(f'    MOV AX, {l}')
            opmap = {
                '+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV', '%': 'MOD',
                '<<': 'SHL', '>>': 'SHR',
                '<': 'CMP', '>': 'CMP', '==': 'CMP', '!=': 'CMP', '<=': 'CMP', '>=': 'CMP',
            }
            instr = opmap.get(op, 'OP')
            asm += [f'    {instr} AX, {r}', f'    MOV {d}, AX']
            continue

        am = re.match(r'(\w+)\s*=\s*(.+)', line)
        if am:
            asm.append(f'    MOV {am.group(1)}, {am.group(2).strip()}')
            continue

        asm.append(f'    ; {line}')
    return {'assembly': asm, 'errors': []}


# =====================================================================
#  ORCHESTRATOR
# =====================================================================
PHASE_DEFS = [
    (1, 'lexical',      'Lexical Analysis',             PHASE1_ROLE, PHASE1_DESC),
    (2, 'syntax',       'Syntax Analysis',              PHASE2_ROLE, PHASE2_DESC),
    (3, 'semantic',     'Semantic Analysis',             PHASE3_ROLE, PHASE3_DESC),
    (4, 'intermediate', 'Intermediate Code Generation',  PHASE4_ROLE, PHASE4_DESC),
    (5, 'optimization', 'Code Optimization',             PHASE5_ROLE, PHASE5_DESC),
    (6, 'codegen',      'Code Generation',               PHASE6_ROLE, PHASE6_DESC),
]


def _skip_from(n):
    out = []
    for num, pid, name, role, desc in PHASE_DEFS:
        if num >= n:
            out.append({
                'id': pid, 'name': name, 'role': role, 'description': desc,
                'output': None, 'errors': [], 'completed': False, 'skipped': True,
            })
    return out


def run_pipeline(source):
    """Run all 6 phases. Return a flat dict consumed by the API endpoint."""
    phases_meta = []      # per-phase metadata list (for the UI tabs)
    all_errors = []       # aggregated errors
    result = {            # flat response keys
        'tokens': [],
        'syntax_tree': None,
        'semantic_tree': None,
        'syntax_tree_ascii': '',
        'semantic_tree_ascii': '',
        'symbol_table': [],
        'ir': [],
        'optimized_ir': [],
        'assembly': [],
        'errors': [],
        'phases': [],
    }

    def _phase(pid, name, role, desc, output, errors, completed=True):
        phases_meta.append({
            'id': pid, 'name': name, 'role': role, 'description': desc,
            'output': output, 'errors': errors, 'completed': completed,
        })
        if errors:
            all_errors.extend(errors)

    # -- 1. Lexical --
    lex = phase_lexical(source)
    result['tokens'] = lex['tokens']
    _phase('lexical', 'Lexical Analysis', PHASE1_ROLE, PHASE1_DESC,
           {'tokens': lex['tokens']}, lex['errors'])
    if lex['errors']:
        phases_meta += _skip_from(2)
        result['phases'] = phases_meta
        result['errors'] = all_errors
        return result

    # -- 2. Syntax --
    syn = phase_syntax(lex['tokens'])
    result['syntax_tree'] = syn['syntax_tree']

    # Generate centered ASCII tree (textbook format) for syntax tree
    stree_ascii = render_ascii_tree(syn['syntax_tree']) if syn['syntax_tree'] else ''
    result['syntax_tree_ascii'] = stree_ascii

    _phase('syntax', 'Syntax Analysis', PHASE2_ROLE, PHASE2_DESC,
           {'syntax_tree': syn['syntax_tree'],
            'syntax_tree_ascii': stree_ascii},
           syn['errors'])
    if syn['errors']:
        phases_meta += _skip_from(3)
        result['phases'] = phases_meta
        result['errors'] = all_errors
        return result

    # -- 3. Semantic --
    sem = phase_semantic(lex['tokens'], syn['syntax_tree'])
    result['symbol_table'] = sem['symbol_table']
    result['semantic_tree'] = sem['semantic_tree']

    # Generate centered ASCII tree with type annotations for semantic tree
    sem_ascii = render_ascii_tree(sem['semantic_tree'], show_types=True) if sem['semantic_tree'] else ''
    result['semantic_tree_ascii'] = sem_ascii

    _phase('semantic', 'Semantic Analysis', PHASE3_ROLE, PHASE3_DESC,
           {'symbol_table': sem['symbol_table'], 'semantic_tree': sem['semantic_tree'],
            'semantic_tree_ascii': sem_ascii},
           sem['errors'])
    if sem['errors']:
        phases_meta += _skip_from(4)
        result['phases'] = phases_meta
        result['errors'] = all_errors
        return result

    # -- 4. Intermediate Code --
    ir = phase_intermediate(lex['tokens'])
    result['ir'] = ir['ir']
    _phase('intermediate', 'Intermediate Code Generation', PHASE4_ROLE, PHASE4_DESC,
           {'tac': ir['ir']}, ir['errors'])
    if ir['errors']:
        phases_meta += _skip_from(5)
        result['phases'] = phases_meta
        result['errors'] = all_errors
        return result

    # -- 5. Optimization --
    opt = phase_optimization(ir['ir'])
    result['optimized_ir'] = opt['optimized_ir']
    _phase('optimization', 'Code Optimization', PHASE5_ROLE, PHASE5_DESC,
           {'optimized_tac': opt['optimized_ir'], 'changes': opt['changes']},
           opt['errors'])
    if opt['errors']:
        phases_meta += _skip_from(6)
        result['phases'] = phases_meta
        result['errors'] = all_errors
        return result

    # -- 6. Code Generation --
    cg = phase_codegen(opt['optimized_ir'])
    result['assembly'] = cg['assembly']
    _phase('codegen', 'Code Generation', PHASE6_ROLE, PHASE6_DESC,
           {'assembly': cg['assembly']}, cg['errors'])

    result['phases'] = phases_meta
    result['errors'] = all_errors
    return result
