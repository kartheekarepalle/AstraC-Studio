import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.services.compiler_pipeline import run_pipeline

r = run_pipeline('int main() { int a = 1; return a; }')

with open('test_output3.txt', 'w', encoding='utf-8') as f:
    f.write(f"Keys: {sorted(r.keys())}\n\n")
    
    f.write(f"=== syntax_tree_ascii ===\n")
    sa = r.get('syntax_tree_ascii', 'MISSING')
    f.write(f"{sa}\n\n")
    
    f.write(f"=== semantic_tree_ascii ===\n")
    sma = r.get('semantic_tree_ascii', 'MISSING')
    f.write(f"{sma}\n\n")
    
    f.write(f"Has syntax_tree_visual? {'syntax_tree_visual' in r}\n")
    f.write(f"Has semantic_tree_visual? {'semantic_tree_visual' in r}\n")
    
    f.write(f"\n=== errors ===\n{r.get('errors', [])}\n")

print("Done - see test_output3.txt")
