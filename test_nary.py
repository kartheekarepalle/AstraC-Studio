import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.services.compiler_pipeline import run_pipeline

code = """int main() {
    int a = 5;
    int b = 10;
    int sum = a + b;
    printf("Sum = %d\\n", sum);
    return 0;
}"""

r = run_pipeline(code)

with open('test_output3.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 70 + "\n")
    f.write("  SYNTAX TREE  (values only)\n")
    f.write("=" * 70 + "\n\n")
    f.write(r.get('syntax_tree_ascii', 'MISSING') + "\n")

    f.write("\n" + "=" * 70 + "\n")
    f.write("  SEMANTIC TREE  (values + types)\n")
    f.write("=" * 70 + "\n\n")
    f.write(r.get('semantic_tree_ascii', 'MISSING') + "\n")

    f.write("\n" + "=" * 70 + "\n")
    f.write("  ERRORS\n")
    f.write("=" * 70 + "\n")
    f.write(str(r.get('errors', [])) + "\n")

print("Done - see test_output3.txt")
