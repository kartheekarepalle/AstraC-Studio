# Test for C Compiler stub pipeline
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/c_compiler')))
from lexer import CLexer
from parser import CParser
from semantic import CSemanticAnalyzer
from ir import CIRGenerator
from optimizer import COptimizer
from codegen import CCodeGenerator

def test_c_pipeline():
    code = "int main() { return 0; }"
    lexer = CLexer(code)
    tokens = lexer.tokenize()
    parser = CParser(tokens)
    ast = parser.parse()
    analyzer = CSemanticAnalyzer()
    analyzer.analyze(ast)
    irgen = CIRGenerator()
    irgen.generate(ast)
    optimizer = COptimizer(irgen.get_instructions())
    optimized = optimizer.optimize()
    codegen = CCodeGenerator(optimized)
    target_code = codegen.generate()
    assert target_code[0].startswith("function main"), "Function definition missing"
    assert "return 0;" in target_code[1], "Return statement missing"

def run_tests():
    test_c_pipeline()
    print("C compiler stub pipeline test passed.")

if __name__ == "__main__":
    run_tests()
