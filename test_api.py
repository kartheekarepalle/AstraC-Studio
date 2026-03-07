import requests, json

r = requests.post('http://127.0.0.1:8001/compile', json={
    'code': 'int main() { int a = 1; return a; }'
}).json()

print("=== KEYS ===")
print(list(r.keys()))

print("\n=== ERRORS ===")
print(r.get('errors', []))

print("\n=== syntax_tree (type) ===")
st = r.get('syntax_tree')
print(type(st))
if st:
    print("label:", st.get('label','?'))

print("\n=== syntax_tree_ascii ===")
sa = r.get('syntax_tree_ascii', '')
print(f"len={len(sa)}")
print("REPR:", repr(sa[:300]))
print("DISPLAY:")
print(sa[:500])

print("\n=== semantic_tree_ascii ===")
sma = r.get('semantic_tree_ascii', '')
print(f"len={len(sma)}")
print("REPR:", repr(sma[:300]))
print("DISPLAY:")
print(sma[:500])
