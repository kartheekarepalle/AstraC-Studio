import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from compiler_pipeline import run_pipeline
from compile_run import TACInterpreter

source = '''#include <stdio.h>
int main() {
    int a[3], b[3], c[3], i;
    for (i = 0; i < 3; i++) { a[i] = i + 1; b[i] = (i + 1) * 10; }
    for (i = 0; i < 3; i++) c[i] = a[i] + b[i];
    for (i = 0; i < 3; i++) printf("%d ", c[i]);
    printf("\\n");
    return 0;
}
'''

r = run_pipeline(source)
print("=== ERRORS ===")
print(r.get('errors'))
print("=== IR ===")
for l in (r.get('ir') or []):
    print(l)
print("=== OPTIMIZED IR ===")
for l in (r.get('optimized_ir') or []):
    print(l)

print("\n=== RUNNING ===")
tac = r.get('optimized_ir') or r.get('ir') or []
interp = TACInterpreter(tac, stdin_text='')
rt = interp.run()
print("STDOUT:", repr(rt['stdout']))
print("STDERR:", repr(rt['stderr']))
