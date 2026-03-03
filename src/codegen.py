# Mini Programming Language Compiler - Target Code Generator

from typing import List, Tuple

class CodeGenerator:
    def __init__(self, instructions: List[Tuple[str, str, str, str]]):
        self.instructions = instructions
        self.output = []

    def generate(self) -> List[str]:
        for instr in self.instructions:
            op, left, right, dest = instr
            if op == 'ASSIGN':
                self.output.append(f"{dest} = {left}")
            elif op in ('+', '-', '*', '/'):
                self.output.append(f"{dest} = {left} {op} {right}")
            else:
                raise Exception(f"Unknown operation: {op}")
        return self.output

if __name__ == "__main__":
    instructions = [('+', '3', '4', 't1'), ('*', 't1', '2', 't2'), ('ASSIGN', 't2', '_', 'x')]
    codegen = CodeGenerator(instructions)
    code = codegen.generate()
    for line in code:
        print(line)
