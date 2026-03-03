# C Compiler - Parser (Stub for C99 grammar)
from typing import List, Tuple, Any
from lexer import CLexer, Token

class CASTNode:
    def __init__(self, type_: str, value: Any = None, children: List['CASTNode'] = None):
        self.type = type_
        self.value = value
        self.children = children or []

    def __repr__(self):
        return f"CASTNode({self.type}, {self.value}, {self.children})"

class CParser:
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

    def parse(self) -> CASTNode:
        # Stub: parse a function definition or declaration
        # Extend this to full C99 grammar incrementally
        return self.function_definition()

    def function_definition(self) -> CASTNode:
        # Example: int main() { return 0; }
        type_spec = self.eat('KEYWORD')
        func_name = self.eat('ID')
        self.eat('LPAREN')
        self.eat('RPAREN')
        self.eat('LBRACE')
        body = self.compound_statement()
        self.eat('RBRACE')
        return CASTNode('FUNC_DEF', func_name[1], [body])

    def compound_statement(self) -> CASTNode:
        # Stub: parse a single return statement
        if self.current()[0] == 'KEYWORD' and self.current()[1] == 'return':
            self.eat('KEYWORD')
            expr = self.eat('NUMBER')
            self.eat('SEMICOLON')
            return CASTNode('RETURN', expr[1])
        else:
            print(f'[Parser Error] Only return statement supported in stub')
            raise SyntaxError('Only return statement supported in stub')
