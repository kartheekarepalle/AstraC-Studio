import requests, json

r = requests.post('http://127.0.0.1:8001/compile', json={
    'code': 'int main() { int a = 1; return a; }'
}).json()

with open('test_output.txt', 'w', encoding='utf-8') as f:
    f.write("=== KEYS ===\n")
    f.write(str(list(r.keys())) + "\n")
    
    f.write("\n=== ERRORS ===\n")
    f.write(str(r.get('errors', [])) + "\n")
    
    f.write("\n=== syntax_tree exists? ===\n")
    st = r.get('syntax_tree')
    f.write(f"{bool(st)}\n")
    if st:
        f.write(f"label: {st.get('label','?')}\n")
    
    f.write("\n=== syntax_tree_ascii ===\n")
    sa = r.get('syntax_tree_ascii', '')
    f.write(f"len={len(sa)}\n")
    f.write(f"REPR: {repr(sa[:300])}\n")
    f.write("DISPLAY:\n")
    f.write(sa[:500] + "\n")
    
    f.write("\n=== semantic_tree_ascii ===\n")
    sma = r.get('semantic_tree_ascii', '')
    f.write(f"len={len(sma)}\n")
    f.write(f"REPR: {repr(sma[:300])}\n")
    f.write("DISPLAY:\n")
    f.write(sma[:500] + "\n")

print("Done - see test_output.txt")
