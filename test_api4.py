import requests, json

r = requests.post('http://127.0.0.1:8001/api/compile-run', json={
    'source': 'int main() { int a = 1; return a; }'
})

with open('test_output3.txt', 'w', encoding='utf-8') as f:
    f.write(f"Status: {r.status_code}\n\n")
    data = r.json()
    
    f.write(f"Keys: {sorted(data.keys())}\n\n")
    
    sa = data.get('syntax_tree_ascii', 'MISSING')
    f.write(f"=== syntax_tree_ascii ===\n")
    f.write(f"{sa}\n\n")
    
    sma = data.get('semantic_tree_ascii', 'MISSING')
    f.write(f"=== semantic_tree_ascii ===\n")
    f.write(f"{sma}\n\n")
    
    f.write(f"Has syntax_tree_visual? {'syntax_tree_visual' in data}\n")
    f.write(f"Has semantic_tree_visual? {'semantic_tree_visual' in data}\n")
    
    f.write(f"\n=== errors ===\n{data.get('errors', [])}\n")

print("Done - see test_output3.txt")
