import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.services.compiler_pipeline import phase_syntax, phase_lexical

code = """int main() {
    int a = 5;
    int b = 10;
    int sum = a + b;
    printf("Sum = %d\\n", sum);
    return 0;
}"""

lex = phase_lexical(code)
syn = phase_syntax(lex['tokens'])
tree = syn['syntax_tree']

with open('test_tree_structure.txt', 'w', encoding='utf-8') as f:
    f.write(json.dumps(tree, indent=2))

print("Tree written to test_tree_structure.txt")
