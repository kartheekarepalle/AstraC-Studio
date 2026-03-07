import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from compiler_pipeline import run_pipeline
from compile_run import TACInterpreter

source = r'''
#include <stdio.h>
int main() {
    int x = 2;
    switch (x) {
    case 1:
        printf("one\n");
        break;
    case 2:
        printf("two\n");
        break;
    default:
        printf("other\n");
    }
    return 0;
}
'''

print("=== Simple switch test ===")
result = run_pipeline(source)
if result.get('errors'):
    print('ERRORS:', result['errors'])
else:
    tac = result.get('optimized_ir') or result.get('ir') or []
    print('TAC:')
    for l in tac:
        print(f'  {l}')
    interp = TACInterpreter(tac)
    rt = interp.run()
    print(f'STDOUT: {rt["stdout"]!r}')
    print(f'EXPECTED: "two\\n"')
    assert rt['stdout'] == 'two\n', f'FAIL: got {rt["stdout"]!r}'
    print('PASS')

# Now test the calculator
print("\n=== Calculator test ===")
source2 = r'''
#include <stdio.h>
#include <float.h>
int main() {
    char op;
    double a, b, res;
    printf("Enter an operator (+, -, *, /): ");
    scanf("%c", &op);
    printf("Enter two operands: ");
    scanf("%lf %lf", &a, &b);
    switch (op) {
    case '+':
        res = a + b;
        break;
    case '-':
        res = a - b;
        break;
    case '*':
         res = a * b;
        break;
    case '/':
        res = a / b;
        break;
    default:
        printf("Error! Incorrect Operator Value\n");
        res = -DBL_MAX;
    }
    if(res!=-DBL_MAX)
      printf("%.2lf", res);
    return 0;
}
'''

result2 = run_pipeline(source2)
if result2.get('errors'):
    print('ERRORS:', result2['errors'])
else:
    tac2 = result2.get('optimized_ir') or result2.get('ir') or []
    print('TAC:')
    for l in tac2:
        print(f'  {l}')
    
    interp2 = TACInterpreter(tac2, stdin_text='+ 5.5 3.2')
    rt2 = interp2.run()
    print(f'Test + 5.5 3.2:')
    print(f'  STDOUT: {rt2["stdout"]!r}')
    print(f'  STDERR: {rt2["stderr"]!r}')
    if '8.70' in rt2['stdout']:
        print('  PASS')
    else:
        print('  FAIL')

    interp3 = TACInterpreter(tac2, stdin_text='* 4 5')
    rt3 = interp3.run()
    print(f'Test * 4 5:')
    print(f'  STDOUT: {rt3["stdout"]!r}')
    if '20.00' in rt3['stdout']:
        print('  PASS')
    else:
        print('  FAIL')

print("\nDone")
