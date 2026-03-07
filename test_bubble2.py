"""Minimal bubble sort debug using real interpreter."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from compiler_pipeline import run_pipeline
from compile_run import TACInterpreter
import re

source = r'''
#include <stdio.h>
int main() {
    int arr[5], i, j, temp;
    arr[0] = 64;
    arr[1] = 34;
    arr[2] = 25;
    arr[3] = 12;
    arr[4] = 22;
    for (i = 0; i < 4; i++) {
        for (j = 0; j < 4; j++) {
            if (arr[j] > arr[j+1]) {
                temp = arr[j];
                arr[j] = arr[j+1];
                arr[j+1] = temp;
            }
        }
    }
    for (i = 0; i < 5; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");
    return 0;
}
'''

result = run_pipeline(source)
tac = result.get('optimized_ir') or result.get('ir') or []

# Patch _eval to trace IF_FALSE conditions with arr
orig_eval = TACInterpreter._eval
call_count = [0]

def traced_eval(self, expr, env):
    val = orig_eval(self, expr, env)
    if 'arr' in expr and '>' in expr:
        call_count[0] += 1
        j = env.get('j', '?')
        i = env.get('i', '?')
        arr = env.get('arr', {})
        lv = arr.get(j, '?') if isinstance(j, int) and isinstance(arr, dict) else '?'
        # try to compute arr[j+1]
        rv = arr.get(j + 1, '?') if isinstance(j, int) and isinstance(arr, dict) else '?'
        print(f"  eval({expr!r}) -> {val}  (i={i}, j={j}, arr[j]={lv}, arr[j+1]={rv})")
    return val

TACInterpreter._eval = traced_eval

interp = TACInterpreter(tac)
rt = interp.run()
print(f"\nOutput: {rt['stdout']!r}")

# Restore
TACInterpreter._eval = orig_eval
