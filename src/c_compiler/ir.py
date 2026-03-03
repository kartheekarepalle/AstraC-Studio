# C Compiler - IR Generation (Stub)
from parser import CASTNode
from typing import List, Tuple

class CIRGenerator:
    def __init__(self):
        self.instructions: List[Tuple[str, str, str, str]] = []

    def generate(self, node: CASTNode):
        if node.type == 'FUNC_DEF':
            self.instructions.append(('FUNC_DEF', node.value, '_', '_'))
            for child in node.children:
                self.generate(child)
        elif node.type == 'RETURN':
            self.instructions.append(('RETURN', node.value, '_', '_'))
        else:
            print(f'[IR Error] Unknown AST node type: {node.type}')
            raise Exception(f'Unknown AST node type: {node.type}')

    def get_instructions(self) -> List[Tuple[str, str, str, str]]:
        return self.instructions
