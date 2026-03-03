# Mini Programming Language Compiler - Main Driver

from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.ir import IRGenerator
from src.optimizer import Optimizer
from src.codegen import CodeGenerator

if __name__ == "__main__":
    code = "x = 3 + 4 * 2;"
    print("Source code:", code)

    # Lexical Analysis
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    print("Tokens:", tokens)

    # Parsing
    parser = Parser(tokens)
    ast = parser.parse()
    print("AST:", ast)

    # Semantic Analysis
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    print("Semantic analysis passed.")

    # IR Generation
    irgen = IRGenerator()
    irgen.generate(ast)
    instructions = irgen.get_instructions()
    print("IR:", instructions)

    # Optimization
    optimizer = Optimizer(instructions)
    optimized = optimizer.optimize()
    print("Optimized IR:", optimized)

    # Code Generation
    codegen = CodeGenerator(optimized)
    target_code = codegen.generate()
    print("Target Code:")
    for line in target_code:
        print(line)
