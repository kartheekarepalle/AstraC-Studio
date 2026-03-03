# C Compiler - Main Driver (Stub Pipeline)
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from lexer import CLexer
from parser import CParser
from semantic import CSemanticAnalyzer
from ir import CIRGenerator
from optimizer import COptimizer
from codegen import CCodeGenerator

if __name__ == "__main__":
    code = "int main() { return 0; }"
    print("Source code:", code)

    # Lexical Analysis
    lexer = CLexer(code)
    tokens = lexer.tokenize()
    print("Tokens:", tokens)

    # Parsing
    parser = CParser(tokens)
    ast = parser.parse()
    print("AST:", ast)

    # Semantic Analysis
    analyzer = CSemanticAnalyzer()
    analyzer.analyze(ast)
    print("Semantic analysis passed.")

    # IR Generation
    irgen = CIRGenerator()
    irgen.generate(ast)
    instructions = irgen.get_instructions()
    print("IR:", instructions)

    # Optimization
    optimizer = COptimizer(instructions)
    optimized = optimizer.optimize()
    print("Optimized IR:", optimized)

    # Code Generation
    codegen = CCodeGenerator(optimized)
    target_code = codegen.generate()
    print("Target Code:")
    for line in target_code:
        print(line)
