import requests, json

code = """int main() {
    int a = 5;
    int b = 10;
    int sum = a + b;
    printf("Sum = %d\\n", sum);
    return 0;
}"""

r = requests.post('http://127.0.0.1:8001/api/compile-run', json={
    'source': code
})

with open('test_output3.txt', 'w', encoding='utf-8') as f:
    data = r.json()
    f.write(f"Status: {r.status_code}\n\n")
    
    f.write("=" * 70 + "\n")
    f.write("  SYNTAX TREE\n")
    f.write("=" * 70 + "\n\n")
    f.write(data.get('syntax_tree_ascii', 'MISSING') + "\n")
    
    f.write("\n" + "=" * 70 + "\n")
    f.write("  SEMANTIC TREE\n")
    f.write("=" * 70 + "\n\n")
    f.write(data.get('semantic_tree_ascii', 'MISSING') + "\n")
    
    f.write(f"\nHas visual keys? syntax_tree_visual={'syntax_tree_visual' in data}, semantic_tree_visual={'semantic_tree_visual' in data}\n")
    f.write(f"Errors: {data.get('errors', [])}\n")

print("Done - see test_output3.txt")
