# C Compiler - Lexer (C99 keywords and tokens)
import re
from typing import List, Tuple

Token = Tuple[str, str]

C_KEYWORDS = [
    'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum', 'extern',
    'float', 'for', 'goto', 'if', 'inline', 'int', 'long', 'register', 'restrict', 'return', 'short', 'signed',
    'sizeof', 'static', 'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while', '_Bool',
    '_Complex', '_Imaginary'
]

class CLexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        token_specification = [
            ('PP_DIRECTIVE', r'\#[^\n]*'),   # preprocessor directives – skip
            ('COMMENT_LINE', r'//[^\n]*'),   # line comments – skip
            ('COMMENT_BLOCK', r'/\*[\s\S]*?\*/'),  # block comments – skip
            ('NUMBER',   r'\d+(\.\d*)?'),
            ('ID',       r'[A-Za-z_]\w*'),
            ('OP',       r'[+\-*/%&|^~!=<>]'),
            ('ASSIGN',   r'='),
            ('SEMICOLON',r';'),
            ('COMMA',    r','),
            ('LPAREN',   r'\('),
            ('RPAREN',   r'\)'),
            ('LBRACE',   r'\{'),
            ('RBRACE',   r'\}'),
            ('LBRACK',   r'\['),
            ('RBRACK',   r'\]'),
            ('STRING',   r'"([^"\\]|\\.)*"'),
            ('CHAR',     r"'([^'\\]|\\.)*'"),
            ('DOT',      r'\.'),
            ('ARROW',    r'->'),
            ('HASH',     r'\#'),
            ('SKIP',     r'[ \t]+'),
            ('NEWLINE',  r'\n'),
            ('MISMATCH', r'.'),
        ]
        tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
        get_token = re.compile(tok_regex).match
        pos = 0
        line = self.source
        mo = get_token(line, pos)
        while mo:
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'ID' and value in C_KEYWORDS:
                self.tokens.append(('KEYWORD', value))
            elif kind == 'ID':
                self.tokens.append(('ID', value))
            elif kind in ['NUMBER', 'OP', 'ASSIGN', 'SEMICOLON', 'COMMA', 'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACK', 'RBRACK', 'STRING', 'CHAR', 'DOT', 'ARROW']:
                self.tokens.append((kind, value))
            elif kind in ('SKIP', 'NEWLINE', 'PP_DIRECTIVE', 'COMMENT_LINE', 'COMMENT_BLOCK', 'HASH'):
                pass  # skip whitespace, preprocessor directives, and comments
            elif kind == 'MISMATCH':
                # Don't crash on unexpected characters – just skip them
                pass
            pos = mo.end()
            mo = get_token(line, pos)
        return self.tokens
