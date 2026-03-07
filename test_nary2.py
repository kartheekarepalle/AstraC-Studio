import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.services.compiler_pipeline import run_pipeline

# Test 1: Simple assignment
code1 = "int main() { int a = 1; return a; }"

# Test 2: Expression with binary ops
code2 = "int main() { int x = 2 + 3 * 4; return x; }"

for i, code in enumerate([code1, code2], 1):
    r = run_pipeline(code)
    with open(f'test_output_t{i}.txt', 'w', encoding='utf-8') as f:
        f.write(f"CODE: {code}\n\n")
        f.write("SYNTAX TREE:\n")
        f.write(r.get('syntax_tree_ascii', 'MISSING') + "\n\n")
        f.write("SEMANTIC TREE:\n")
        f.write(r.get('semantic_tree_ascii', 'MISSING') + "\n")
    print(f"Test {i} done")

print("See test_output_t1.txt and test_output_t2.txt")
