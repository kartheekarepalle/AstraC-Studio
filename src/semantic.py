# Mini Programming Language Compiler - Semantic Analyzer

from src.parser import ASTNode

class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = {}

    def analyze(self, node: ASTNode):
        if node.type == 'ASSIGN':
            var_name = node.value
            expr = node.children[0]
            value_type = self.analyze(expr)
            self.symbol_table[var_name] = value_type
            return value_type
        elif node.type == 'BINOP':
            left_type = self.analyze(node.children[0])
            right_type = self.analyze(node.children[1])
            if left_type != 'number' or right_type != 'number':
                print('[Semantic Error] Operands must be numbers')
                raise TypeError('Operands must be numbers')
            return 'number'
        elif node.type == 'NUMBER':
            return 'number'
        elif node.type == 'ID':
            var_name = node.value
            if var_name not in self.symbol_table:
                print(f'[Semantic Error] Undefined variable: {var_name}')
                raise NameError(f'Undefined variable: {var_name}')
            return self.symbol_table[var_name]
        else:
            print(f'[Semantic Error] Unknown AST node type: {node.type}')
            raise Exception(f'Unknown AST node type: {node.type}')

if __name__ == "__main__":
    from src.parser import Parser
    from src.lexer import Lexer
    code = "x = 3 + 4;"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    print("Semantic analysis passed.")
