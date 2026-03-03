# Mini Programming Language Compiler - Intermediate Representation (IR)

from src.parser import ASTNode
from typing import List, Tuple

class IRGenerator:
    def __init__(self):
        self.instructions: List[Tuple[str, str, str, str]] = []
        self.temp_count = 0

    def new_temp(self) -> str:
        self.temp_count += 1
        return f"t{self.temp_count}"

    def generate(self, node: ASTNode) -> str:
        if node.type == 'ASSIGN':
            temp = self.generate(node.children[0])
            self.instructions.append(('ASSIGN', temp, '_', node.value))
            return node.value
        elif node.type == 'BINOP':
            left = self.generate(node.children[0])
            right = self.generate(node.children[1])
            temp = self.new_temp()
            self.instructions.append((node.value, left, right, temp))
            return temp
        elif node.type == 'NUMBER' or node.type == 'ID':
            return node.value
        else:
            print(f'[IR Error] Unknown AST node type: {node.type}')
            raise Exception(f'Unknown AST node type: {node.type}')

    def get_instructions(self) -> List[Tuple[str, str, str, str]]:
        return self.instructions

if __name__ == "__main__":
    from src.parser import Parser
    from src.lexer import Lexer
    code = "x = 3 + 4 * 2;"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    irgen = IRGenerator()
    irgen.generate(ast)
    for instr in irgen.get_instructions():
        print(instr)
