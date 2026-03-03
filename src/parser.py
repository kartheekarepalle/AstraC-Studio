# Mini Programming Language Compiler - Parser

from typing import List, Tuple, Any
from src.lexer import Lexer, Token

class ASTNode:
    def __init__(self, type_: str, value: Any = None, children: List['ASTNode'] = None):
        self.type = type_
        self.value = value
        self.children = children or []

    def __repr__(self):
        return f"ASTNode({self.type}, {self.value}, {self.children})"

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ('EOF', '')

    def eat(self, token_type: str) -> Token:
        token = self.current()
        if token[0] == token_type:
            self.pos += 1
            return token
        print(f'[Parser Error] Expected {token_type}, got {token}')
        raise SyntaxError(f"Expected {token_type}, got {token}")

    def parse(self) -> ASTNode:
        return self.statement()

    def statement(self) -> ASTNode:
        # Only assignment for now: ID = expr;
        id_token = self.eat('ID')
        self.eat('ASSIGN')
        expr = self.expr()
        self.eat('END')
        return ASTNode('ASSIGN', id_token[1], [expr])

    def expr(self) -> ASTNode:
        node = self.term()
        while self.current()[0] == 'OP' and self.current()[1] in ('+', '-'):
            op = self.eat('OP')
            right = self.term()
            node = ASTNode('BINOP', op[1], [node, right])
        return node

    def term(self) -> ASTNode:
        node = self.factor()
        while self.current()[0] == 'OP' and self.current()[1] in ('*', '/'):
            op = self.eat('OP')
            right = self.factor()
            node = ASTNode('BINOP', op[1], [node, right])
        return node

    def factor(self) -> ASTNode:
        token = self.current()
        if token[0] == 'NUMBER':
            self.eat('NUMBER')
            return ASTNode('NUMBER', token[1])
        elif token[0] == 'ID':
            self.eat('ID')
            return ASTNode('ID', token[1])
        elif token[0] == 'LPAREN':
            self.eat('LPAREN')
            node = self.expr()
            self.eat('RPAREN')
            return node
        else:
            print(f'[Parser Error] Unexpected token: {token}')
            raise SyntaxError(f"Unexpected token: {token}")

if __name__ == "__main__":
    code = "x = 3 + 4 * (2 - 1);"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    print(ast)
