# Mini Programming Language Compiler - Lexer

import re
from typing import List, Tuple, Optional

Token = Tuple[str, str]

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.current = 0

    def tokenize(self) -> List[Token]:
        token_specification = [
            ('NUMBER',   r'\d+(\.\d*)?'),
            ('ID',       r'[A-Za-z_]\w*'),
            ('ASSIGN',   r'='),
            ('END',      r';'),
            ('OP',       r'[+\-*/]'),
            ('LPAREN',   r'\('),
            ('RPAREN',   r'\)'),
            ('SKIP',     r'[ \t]+'),
            ('NEWLINE',  r'\n'),
            ('MISMATCH', r'.'),
        ]
        tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
        get_token = re.compile(tok_regex).match
        line = self.source
        pos = 0
        mo = get_token(line, pos)
        while mo:
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'NUMBER':
                self.tokens.append(('NUMBER', value))
            elif kind == 'ID':
                self.tokens.append(('ID', value))
            elif kind == 'ASSIGN':
                self.tokens.append(('ASSIGN', value))
            elif kind == 'END':
                self.tokens.append(('END', value))
            elif kind == 'OP':
                self.tokens.append(('OP', value))
            elif kind == 'LPAREN':
                self.tokens.append(('LPAREN', value))
            elif kind == 'RPAREN':
                self.tokens.append(('RPAREN', value))
            elif kind == 'NEWLINE' or kind == 'SKIP':
                pass
            elif kind == 'MISMATCH':
                print(f'[Lexer Error] Unexpected character: {value}')
                raise RuntimeError(f'Unexpected character: {value}')
            pos = mo.end()
            mo = get_token(line, pos)
        return self.tokens

if __name__ == "__main__":
    code = "x = 3 + 4;"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    print(tokens)
