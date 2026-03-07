import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'app', 'services'))
from compiler_pipeline import phase_lexical, phase_intermediate, phase_optimization

tests = [
    ('Hello World', 'int main() { printf("Hello World"); return 0; }'),
    ('Simple swap', 'int main() { int a, b, t; scanf("%d %d", &a, &b); t = a; a = b; b = t; printf("%d %d", a, b); return 0; }'),
    ('Factorial', 'int main() { int n, f, i; scanf("%d", &n); f = 1; for(i=1; i<=n; i++) { f = f * i; } printf("%d", f); return 0; }'),
    ('Fibonacci', 'int main() { int n, a, b, c, i; scanf("%d", &n); a = 0; b = 1; for(i=2; i<=n; i++) { c = a + b; a = b; b = c; } printf("%d", b); return 0; }'),
    ('Empty main', 'int main() { return 0; }'),
]
for label, code in tests:
    lex = phase_lexical(code)
    ir = phase_intermediate(lex['tokens'])
    opt = phase_optimization(ir['ir'])
    print(f'{label}: {len(opt["changes"])} optimizations')
    for c in opt['changes']:
        print(f'  [{c["rule"]}] {c["original"]} -> {c["optimized"]}')
