import requests, json

r = requests.post('http://127.0.0.1:8001/compile', json={
    'code': 'int main() { int a = 1; return a; }'
})

with open('test_output2.txt', 'w', encoding='utf-8') as f:
    f.write(f"Status: {r.status_code}\n")
    f.write(f"Response:\n{json.dumps(r.json(), indent=2)}\n")

print("Done - see test_output2.txt")
