import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from compiler_pipeline import run_pipeline
from compile_run import TACInterpreter

# Test 1: scanf with two integers
source = r'''
#include <stdio.h>
int main() {
    int a, b;
    printf("Enter two integers: ");
    scanf("%d %d", &a, &b);
    printf("Sum: %d\n", a + b);
    return 0;
}
'''

print("=== Test 1: scanf sum ===")
result = run_pipeline(source)
tac = result.get('optimized_ir') or result.get('ir') or []
print("TAC:")
for l in tac:
    print(" ", l)

interp = TACInterpreter(tac, stdin_text='10 20')
rt = interp.run()
print("stdout:", repr(rt['stdout']))
print("stderr:", repr(rt['stderr']))
print("exit:", rt['exit_code'])
expected = "Enter two integers: Sum: 30\n"
print("PASS" if rt['stdout'] == expected else f"FAIL (expected {expected!r})")

# Test 2: scanf with float
source2 = r'''
#include <stdio.h>
int main() {
    float x;
    scanf("%f", &x);
    printf("Value: %f\n", x);
    return 0;
}
'''
print("\n=== Test 2: scanf float ===")
result2 = run_pipeline(source2)
tac2 = result2.get('optimized_ir') or result2.get('ir') or []
interp2 = TACInterpreter(tac2, stdin_text='3.14')
rt2 = interp2.run()
print("stdout:", repr(rt2['stdout']))

# Test 3: multiple scanf calls
source3 = r'''
#include <stdio.h>
int main() {
    int a, b, c;
    scanf("%d", &a);
    scanf("%d", &b);
    scanf("%d", &c);
    printf("%d %d %d\n", a, b, c);
    return 0;
}
'''
print("\n=== Test 3: multiple scanf ===")
result3 = run_pipeline(source3)
tac3 = result3.get('optimized_ir') or result3.get('ir') or []
interp3 = TACInterpreter(tac3, stdin_text='100 200 300')
rt3 = interp3.run()
print("stdout:", repr(rt3['stdout']))
expected3 = "100 200 300\n"
print("PASS" if rt3['stdout'] == expected3 else f"FAIL (expected {expected3!r})")

# Test 4: no stdin provided (should use defaults)
print("\n=== Test 4: no stdin ===")
interp4 = TACInterpreter(tac, stdin_text='')
rt4 = interp4.run()
print("stdout:", repr(rt4['stdout']))
print("Should show Sum: 0 (defaults)")
