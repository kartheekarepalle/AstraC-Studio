# Tests for Mini Programming Language Compiler

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.ir import IRGenerator
from src.optimizer import Optimizer
from src.codegen import CodeGenerator

def test_basic_assignment():
    code = "x = 1 + 2 * 3;"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    irgen = IRGenerator()
    irgen.generate(ast)
    optimizer = Optimizer(irgen.get_instructions())
    optimized = optimizer.optimize()
    codegen = CodeGenerator(optimized)
    target_code = codegen.generate()
    assert target_code[-1] == "x = t2" or target_code[-1] == "x = t3"

def run_tests():
    test_basic_assignment()
    print("All tests passed.")

if __name__ == "__main__":
    run_tests()
