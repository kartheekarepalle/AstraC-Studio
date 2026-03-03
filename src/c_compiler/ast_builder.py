# AST Builder — Builds an Abstract Syntax Tree from the C lexer token stream.
# Handles: functions, declarations, assignments, if/else, while, for, return,
# function calls, expressions, structs, arrays, and nested blocks.

from typing import List, Tuple, Optional, Any

Token = Tuple[str, str]


def _ast_node(type_: str, value: str = '', children: list = None) -> dict:
    """Create an AST node dict matching the frontend contract."""
    node = {'type': type_, 'value': value}
    if children:
        node['children'] = children
    else:
        node['children'] = []
    return node


class ASTBuilder:
    """
    Recursive-descent parser that converts a CLexer token list into a JSON-
    serializable AST.  Designed to be *resilient*: on unexpected tokens it
    skips ahead rather than crashing, so every valid program produces a tree
    and malformed programs still yield a partial tree.
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # ── helpers ───────────────────────────────────────────────────────

    def _cur(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ('EOF', '')

    def _peek(self, offset=1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return ('EOF', '')

    def _eat(self, kind: str = None) -> Token:
        tok = self._cur()
        if kind and tok[0] != kind:
            return tok  # don't advance – let caller handle
        self.pos += 1
        return tok

    def _match(self, kind: str, value: str = None) -> bool:
        tok = self._cur()
        if tok[0] != kind:
            return False
        if value is not None and tok[1] != value:
            return False
        return True

    def _expect(self, kind: str, value: str = None) -> Token:
        if self._match(kind, value):
            return self._eat()
        return self._cur()

    TYPE_KEYWORDS = {
        'int', 'float', 'double', 'char', 'void', 'long', 'short',
        'unsigned', 'signed', 'struct', 'union', 'enum', 'const',
        'static', 'extern', 'register', 'volatile', 'inline', '_Bool',
    }

    def _is_type_start(self) -> bool:
        tok = self._cur()
        return tok[0] == 'KEYWORD' and tok[1] in self.TYPE_KEYWORDS

    # ── public entry ──────────────────────────────────────────────────

    def build(self) -> dict:
        children = []
        while self._cur()[0] != 'EOF':
            node = self._top_level()
            if node:
                children.append(node)
            else:
                self.pos += 1  # skip unparsable token
        return _ast_node('Program', '', children)

    # ── top level ─────────────────────────────────────────────────────

    def _top_level(self) -> Optional[dict]:
        if self._is_type_start():
            return self._declaration_or_function()
        # skip unknown top-level tokens
        return None

    def _declaration_or_function(self) -> dict:
        start = self.pos
        type_str = self._consume_type()

        # pointer stars
        while self._match('OP', '*'):
            type_str += '*'
            self._eat()

        if not self._match('ID'):
            self.pos = start + 1
            return _ast_node('Unknown', type_str)

        name_tok = self._eat('ID')
        name = name_tok[1]

        # function?
        if self._match('LPAREN'):
            return self._function_def(type_str, name)

        # global declaration
        return self._var_declaration_rest(type_str, name)

    def _consume_type(self) -> str:
        parts = []
        while self._is_type_start():
            parts.append(self._eat()[1])
        return ' '.join(parts) if parts else 'int'

    # ── function definition ───────────────────────────────────────────

    def _function_def(self, ret_type: str, name: str) -> dict:
        self._expect('LPAREN')
        params = self._param_list()
        self._expect('RPAREN')

        if self._match('LBRACE'):
            body = self._block()
        else:
            # forward declaration
            self._expect('SEMICOLON')
            body = _ast_node('Block')

        return _ast_node('FunctionDef', f'{ret_type} {name}',
                         [_ast_node('Parameters', '', params), body])

    def _param_list(self) -> list:
        params = []
        while not self._match('RPAREN') and self._cur()[0] != 'EOF':
            if self._match('COMMA'):
                self._eat()
            p = self._param()
            if p:
                params.append(p)
        return params

    def _param(self) -> Optional[dict]:
        if not self._is_type_start():
            return None
        t = self._consume_type()
        while self._match('OP', '*'):
            t += '*'
            self._eat()
        n = ''
        if self._match('ID'):
            n = self._eat('ID')[1]
        # arrays in params  e.g. int arr[]
        if self._match('LBRACK'):
            self._eat()
            self._expect('RBRACK')
            t += '[]'
        return _ast_node('Param', f'{t} {n}'.strip())

    # ── block ─────────────────────────────────────────────────────────

    def _block(self) -> dict:
        self._expect('LBRACE')
        stmts = []
        while not self._match('RBRACE') and self._cur()[0] != 'EOF':
            s = self._statement()
            if s:
                stmts.append(s)
        self._expect('RBRACE')
        return _ast_node('Block', '', stmts)

    # ── statements ────────────────────────────────────────────────────

    def _statement(self) -> Optional[dict]:
        cur = self._cur()

        if cur[0] == 'KEYWORD':
            kw = cur[1]
            if kw == 'return':
                return self._return_stmt()
            if kw == 'if':
                return self._if_stmt()
            if kw == 'while':
                return self._while_stmt()
            if kw == 'for':
                return self._for_stmt()
            if kw == 'do':
                return self._do_while_stmt()
            if kw == 'switch':
                return self._switch_stmt()
            if kw == 'break':
                self._eat()
                self._expect('SEMICOLON')
                return _ast_node('Break')
            if kw == 'continue':
                self._eat()
                self._expect('SEMICOLON')
                return _ast_node('Continue')
            if kw in self.TYPE_KEYWORDS:
                return self._local_declaration()

        if cur[0] == 'LBRACE':
            return self._block()

        # expression statement
        return self._expr_statement()

    def _return_stmt(self) -> dict:
        self._expect('KEYWORD', 'return')
        if self._match('SEMICOLON'):
            self._eat()
            return _ast_node('Return')
        expr = self._expression()
        self._expect('SEMICOLON')
        return _ast_node('Return', '', [expr])

    def _if_stmt(self) -> dict:
        self._expect('KEYWORD', 'if')
        self._expect('LPAREN')
        cond = self._expression()
        self._expect('RPAREN')
        then_body = self._statement_or_block()
        children = [_ast_node('Condition', '', [cond]), _ast_node('Then', '', [then_body] if then_body else [])]
        if self._match('KEYWORD', 'else'):
            self._eat()
            else_body = self._statement_or_block()
            children.append(_ast_node('Else', '', [else_body] if else_body else []))
        return _ast_node('If', '', children)

    def _while_stmt(self) -> dict:
        self._expect('KEYWORD', 'while')
        self._expect('LPAREN')
        cond = self._expression()
        self._expect('RPAREN')
        body = self._statement_or_block()
        return _ast_node('While', '', [_ast_node('Condition', '', [cond]), body] if body else [_ast_node('Condition', '', [cond])])

    def _for_stmt(self) -> dict:
        self._expect('KEYWORD', 'for')
        self._expect('LPAREN')
        # init
        init = self._for_init()
        # cond
        cond = None
        if not self._match('SEMICOLON'):
            cond = self._expression()
        self._expect('SEMICOLON')
        # update
        update = None
        if not self._match('RPAREN'):
            update = self._expression()
        self._expect('RPAREN')
        body = self._statement_or_block()
        children = [_ast_node('Init', '', [init] if init else [])]
        children.append(_ast_node('Condition', '', [cond] if cond else []))
        children.append(_ast_node('Update', '', [update] if update else []))
        if body:
            children.append(body)
        return _ast_node('For', '', children)

    def _for_init(self) -> Optional[dict]:
        if self._match('SEMICOLON'):
            self._eat()
            return None
        if self._is_type_start():
            return self._local_declaration()
        expr = self._expression()
        self._expect('SEMICOLON')
        return expr

    def _do_while_stmt(self) -> dict:
        self._expect('KEYWORD', 'do')
        body = self._statement_or_block()
        self._expect('KEYWORD', 'while')
        self._expect('LPAREN')
        cond = self._expression()
        self._expect('RPAREN')
        self._expect('SEMICOLON')
        return _ast_node('DoWhile', '', [body, _ast_node('Condition', '', [cond])] if body else [_ast_node('Condition', '', [cond])])

    def _switch_stmt(self) -> dict:
        self._expect('KEYWORD', 'switch')
        self._expect('LPAREN')
        expr = self._expression()
        self._expect('RPAREN')
        self._expect('LBRACE')
        children = [expr]
        while not self._match('RBRACE') and self._cur()[0] != 'EOF':
            if self._match('KEYWORD', 'case'):
                self._eat()
                val = self._expression()
                self._expect('OP')  # colon is sometimes OP ':'
                children.append(_ast_node('Case', '', [val]))
            elif self._match('KEYWORD', 'default'):
                self._eat()
                self._expect('OP')  # ':'
                children.append(_ast_node('Default'))
            else:
                s = self._statement()
                if s:
                    children.append(s)
                else:
                    self.pos += 1
        self._expect('RBRACE')
        return _ast_node('Switch', '', children)

    def _statement_or_block(self) -> Optional[dict]:
        if self._match('LBRACE'):
            return self._block()
        return self._statement()

    def _local_declaration(self) -> dict:
        type_str = self._consume_type()
        while self._match('OP', '*'):
            type_str += '*'
            self._eat()

        if not self._match('ID'):
            self._skip_to_semicolon()
            return _ast_node('Declaration', type_str)

        name = self._eat('ID')[1]
        return self._var_declaration_rest(type_str, name)

    def _var_declaration_rest(self, type_str: str, name: str) -> dict:
        # array?
        if self._match('LBRACK'):
            self._eat()
            size = ''
            if not self._match('RBRACK'):
                size = self._cur()[1]
                self._eat()
            self._expect('RBRACK')
            type_str += f'[{size}]'

        # initializer?
        children = []
        if self._cur()[1] == '=':
            self._eat()  # '='
            if self._match('LBRACE'):
                init = self._initializer_list()
            else:
                init = self._expression()
            children.append(_ast_node('Initializer', '', [init]))

        self._expect('SEMICOLON')
        return _ast_node('Declaration', f'{type_str} {name}', children)

    def _initializer_list(self) -> dict:
        self._expect('LBRACE')
        items = []
        while not self._match('RBRACE') and self._cur()[0] != 'EOF':
            if self._match('COMMA'):
                self._eat()
                continue
            items.append(self._expression())
        self._expect('RBRACE')
        return _ast_node('InitList', '', items)

    def _expr_statement(self) -> dict:
        expr = self._expression()
        self._expect('SEMICOLON')
        return _ast_node('ExprStatement', '', [expr])

    # ── expressions (precedence climbing) ─────────────────────────────

    def _expression(self) -> dict:
        return self._assignment()

    def _assignment(self) -> dict:
        left = self._ternary()
        if self._cur()[1] in ('=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^='):
            op = self._eat()[1]
            right = self._assignment()  # right-to-left
            return _ast_node('Assignment', op, [left, right])
        return left

    def _ternary(self) -> dict:
        node = self._logical_or()
        # skip ternary for simplicity
        return node

    def _logical_or(self) -> dict:
        node = self._logical_and()
        while self._cur()[1] == '|' and self._peek()[1] == '|':
            self._eat()
            self._eat()
            right = self._logical_and()
            node = _ast_node('BinaryOp', '||', [node, right])
        return node

    def _logical_and(self) -> dict:
        node = self._bitwise_or()
        while self._cur()[1] == '&' and self._peek()[1] == '&':
            self._eat()
            self._eat()
            right = self._bitwise_or()
            node = _ast_node('BinaryOp', '&&', [node, right])
        return node

    def _bitwise_or(self) -> dict:
        node = self._bitwise_xor()
        while self._cur()[1] == '|' and self._peek()[1] != '|':
            self._eat()
            right = self._bitwise_xor()
            node = _ast_node('BinaryOp', '|', [node, right])
        return node

    def _bitwise_xor(self) -> dict:
        node = self._bitwise_and()
        while self._cur()[1] == '^':
            self._eat()
            right = self._bitwise_and()
            node = _ast_node('BinaryOp', '^', [node, right])
        return node

    def _bitwise_and(self) -> dict:
        node = self._equality()
        while self._cur()[1] == '&' and self._peek()[1] != '&':
            self._eat()
            right = self._equality()
            node = _ast_node('BinaryOp', '&', [node, right])
        return node

    def _equality(self) -> dict:
        node = self._relational()
        while self._cur()[1] in ('=', '!') and self._peek()[1] == '=':
            op1 = self._eat()[1]
            op2 = self._eat()[1]
            right = self._relational()
            node = _ast_node('BinaryOp', op1 + op2, [node, right])
        return node

    def _relational(self) -> dict:
        node = self._shift()
        while self._cur()[1] in ('<', '>'):
            op = self._eat()[1]
            if self._cur()[1] == '=':
                op += self._eat()[1]
            right = self._shift()
            node = _ast_node('BinaryOp', op, [node, right])
        return node

    def _shift(self) -> dict:
        node = self._additive()
        # skip shift ops for simplicity
        return node

    def _additive(self) -> dict:
        node = self._multiplicative()
        while self._cur()[1] in ('+', '-'):
            op = self._eat()[1]
            right = self._multiplicative()
            node = _ast_node('BinaryOp', op, [node, right])
        return node

    def _multiplicative(self) -> dict:
        node = self._unary()
        while self._cur()[1] in ('*', '/', '%'):
            op = self._eat()[1]
            right = self._unary()
            node = _ast_node('BinaryOp', op, [node, right])
        return node

    def _unary(self) -> dict:
        cur = self._cur()
        if cur[1] in ('-', '!', '~', '&', '*') and cur[0] == 'OP':
            op = self._eat()[1]
            operand = self._unary()
            return _ast_node('UnaryOp', op, [operand])
        if cur[0] == 'KEYWORD' and cur[1] == 'sizeof':
            self._eat()
            if self._match('LPAREN'):
                self._eat()
                inner = self._expression()
                self._expect('RPAREN')
            else:
                inner = self._unary()
            return _ast_node('Sizeof', '', [inner])
        # cast: (type) expr — skip for simplicity
        return self._postfix()

    def _postfix(self) -> dict:
        node = self._primary()
        while True:
            if self._match('LPAREN'):
                # function call
                self._eat()
                args = []
                while not self._match('RPAREN') and self._cur()[0] != 'EOF':
                    if self._match('COMMA'):
                        self._eat()
                        continue
                    args.append(self._expression())
                self._expect('RPAREN')
                node = _ast_node('FunctionCall', node.get('value', ''), args)
            elif self._match('LBRACK'):
                self._eat()
                idx = self._expression()
                self._expect('RBRACK')
                node = _ast_node('ArrayAccess', '', [node, idx])
            elif self._match('DOT'):
                self._eat()
                member = self._eat('ID')[1] if self._match('ID') else '?'
                node = _ast_node('MemberAccess', member, [node])
            elif self._match('ARROW'):
                self._eat()
                member = self._eat('ID')[1] if self._match('ID') else '?'
                node = _ast_node('ArrowAccess', member, [node])
            elif self._cur()[1] in ('+', '-') and self._peek()[1] == self._cur()[1]:
                op = self._eat()[1]
                self._eat()
                node = _ast_node('PostfixOp', op + op, [node])
            else:
                break
        return node

    def _primary(self) -> dict:
        cur = self._cur()
        if cur[0] == 'NUMBER':
            self._eat()
            return _ast_node('Number', cur[1])
        if cur[0] == 'STRING':
            self._eat()
            return _ast_node('String', cur[1])
        if cur[0] == 'CHAR':
            self._eat()
            return _ast_node('Char', cur[1])
        if cur[0] == 'ID':
            self._eat()
            return _ast_node('Identifier', cur[1])
        if cur[0] == 'LPAREN':
            self._eat()
            expr = self._expression()
            self._expect('RPAREN')
            return expr
        if cur[0] == 'KEYWORD' and cur[1] == 'NULL':
            self._eat()
            return _ast_node('Null', 'NULL')
        # fallback
        self._eat()
        return _ast_node('Token', cur[1])

    # ── utilities ─────────────────────────────────────────────────────

    def _skip_to_semicolon(self):
        while self._cur()[0] != 'EOF' and not self._match('SEMICOLON'):
            self.pos += 1
        if self._match('SEMICOLON'):
            self._eat()


def build_ast_from_tokens(tokens: List[Token]) -> dict:
    """Public helper: given a CLexer token list, return a JSON-serializable AST."""
    builder = ASTBuilder(tokens)
    return builder.build()
