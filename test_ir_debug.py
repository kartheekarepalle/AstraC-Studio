"""Diagnose IR vs optimized IR to find optimizer bugs."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from compiler_pipeline import run_pipeline

# Test 1: Array - check if optimizer removes array stores
source1 = r'''
#include <stdio.h>
int main() {
    int arr[5];
    arr[0] = 10;
    arr[1] = 25;
    arr[2] = 5;
    arr[3] = 40;
    arr[4] = 15;
    int max = arr[0];
    printf("Max: %d\n", max);
    return 0;
}
'''
r = run_pipeline(source1)
print("=== Array IR (unoptimized) ===")
for l in (r.get('ir') or []):
    print(" ", l)
print("\n=== Array IR (optimized) ===")
for l in (r.get('optimized_ir') or []):
    print(" ", l)

# Test 2: Nested loop - check operator precedence
source2 = r'''
#include <stdio.h>
int main() {
    int sum = 0;
    int i, j;
    for (i = 1; i <= 3; i++) {
        for (j = 1; j <= 3; j++) {
            sum = sum + i * j;
        }
    }
    printf("Sum: %d\n", sum);
    return 0;
}
'''
r2 = run_pipeline(source2)
print("\n=== Nested Loop IR (unoptimized) ===")
for l in (r2.get('ir') or []):
    print(" ", l)
print("\n=== Nested Loop IR (optimized) ===")
for l in (r2.get('optimized_ir') or []):
    print(" ", l)

# Test 3: Simple array with scanf
source3 = r'''
#include <stdio.h>
int main() {
    int n, i, sum;
    n = 5;
    sum = 0;
    int arr[5];
    arr[0] = 1;
    arr[1] = 2;
    arr[2] = 3;
    arr[3] = 4;
    arr[4] = 5;
    for (i = 0; i < n; i++) {
        sum = sum + arr[i];
    }
    printf("Sum: %d\n", sum);
    return 0;
}
'''
r3 = run_pipeline(source3)
print("\n=== Array sum IR (unoptimized) ===")
for l in (r3.get('ir') or []):
    print(" ", l)
print("\n=== Array sum IR (optimized) ===")
for l in (r3.get('optimized_ir') or []):
    print(" ", l)
