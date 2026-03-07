"""Test switch-case support."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from compiler_pipeline import run_pipeline
from compile_run import TACInterpreter

source = r'''
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

result = run_pipeline(source)
if result.get('errors'):
    print('COMPILE ERRORS:', result['errors'])
else:
    tac = result.get('optimized_ir') or result.get('ir') or []
    print('TAC:')
    for l in tac:
        print(f'  {l}')
    
    # Test addition: + 5.5 3.2 => 8.70
    print('\n--- Test: + 5.5 3.2 ---')
    interp = TACInterpreter(tac, stdin_text='+ 5.5 3.2')
    rt = interp.run()
    print(f'STDOUT: {rt["stdout"]!r}')
    print(f'STDERR: {rt["stderr"]!r}')
    expected = 'Enter an operator (+, -, *, /): Enter two operands: 8.70'
    if expected in rt['stdout']:
        print('PASS')
    else:
        print(f'FAIL: expected {expected!r}')

    # Test multiplication: * 4 5 => 20.00
    print('\n--- Test: * 4 5 ---')
    interp2 = TACInterpreter(tac, stdin_text='* 4 5')
    rt2 = interp2.run()
    print(f'STDOUT: {rt2["stdout"]!r}')
    expected2 = '20.00'
    if expected2 in rt2['stdout']:
        print('PASS')
    else:
        print(f'FAIL: expected contains {expected2!r}')

    # Test division: / 10 3 => 3.33
    print('\n--- Test: / 10 3 ---')
    interp3 = TACInterpreter(tac, stdin_text='/ 10 3')
    rt3 = interp3.run()
    print(f'STDOUT: {rt3["stdout"]!r}')
    expected3 = '3.33'
    if expected3 in rt3['stdout']:
        print('PASS')
    else:
        print(f'FAIL: expected contains {expected3!r}')

    # Test invalid: x 1 2 => Error message
    print('\n--- Test: x 1 2 ---')
    interp4 = TACInterpreter(tac, stdin_text='x 1 2')
    rt4 = interp4.run()
    print(f'STDOUT: {rt4["stdout"]!r}')
    if 'Error!' in rt4['stdout']:
        print('PASS')
    else:
        print(f'FAIL: expected Error! message')
