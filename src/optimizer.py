# Mini Programming Language Compiler - Optimizer

from typing import List, Tuple

class Optimizer:
    def __init__(self, instructions: List[Tuple[str, str, str, str]]):
        self.instructions = instructions

    def constant_folding(self) -> List[Tuple[str, str, str, str]]:
        optimized = []
        for instr in self.instructions:
            op, left, right, dest = instr
            if op in ('+', '-', '*', '/') and left.isdigit() and right.isdigit():
                result = str(eval(f'{left}{op}{right}'))
                optimized.append(('ASSIGN', result, '_', dest))
            else:
                optimized.append(instr)
        return optimized

    def optimize(self) -> List[Tuple[str, str, str, str]]:
        return self.constant_folding()

if __name__ == "__main__":
    # Example usage
    instructions = [('+', '3', '4', 't1'), ('*', 't1', '2', 't2'), ('ASSIGN', 't2', '_', 'x')]
    optimizer = Optimizer(instructions)
    optimized = optimizer.optimize()
    for instr in optimized:
        print(instr)
