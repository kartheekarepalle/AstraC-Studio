"""Comprehensive test of TAC interpreter with many program types."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from compiler_pipeline import run_pipeline
from compile_run import TACInterpreter

def test(name, source, stdin='', expected_contains=None):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    result = run_pipeline(source)
    errors = result.get('errors', [])
    if errors:
        print(f"  COMPILE ERRORS: {errors}")
        return
    tac = result.get('optimized_ir') or result.get('ir') or []
    print(f"  TAC ({len(tac)} lines):")
    for l in tac:
        print(f"    {l}")
    interp = TACInterpreter(tac, stdin_text=stdin)
    rt = interp.run()
    print(f"  stdout: {rt['stdout']!r}")
    print(f"  stderr: {rt['stderr']!r}")
    print(f"  exit:   {rt['exit_code']}")
    if expected_contains:
        for exp in expected_contains:
            if exp in rt['stdout']:
                print(f"  PASS: contains {exp!r}")
            else:
                print(f"  FAIL: missing {exp!r}")

# 1) Array: find max/min
test("Array max/min", r'''
#include <stdio.h>
int main() {
    int arr[5];
    int i, max, min;
    arr[0] = 10;
    arr[1] = 25;
    arr[2] = 5;
    arr[3] = 40;
    arr[4] = 15;
    max = arr[0];
    min = arr[0];
    for (i = 1; i < 5; i++) {
        if (arr[i] > max) {
            max = arr[i];
        }
        if (arr[i] < min) {
            min = arr[i];
        }
    }
    printf("Maximum element is: %d\n", max);
    printf("Minimum element is: %d\n", min);
    return 0;
}
''', expected_contains=["Maximum element is: 40", "Minimum element is: 5"])

# 2) Fibonacci
test("Fibonacci", r'''
#include <stdio.h>
int main() {
    int n, a, b, c, i;
    n = 10;
    a = 0;
    b = 1;
    printf("%d ", a);
    printf("%d ", b);
    for (i = 2; i < n; i++) {
        c = a + b;
        printf("%d ", c);
        a = b;
        b = c;
    }
    printf("\n");
    return 0;
}
''', expected_contains=["0 1 1 2 3 5 8 13 21 34"])

# 3) Factorial with function
test("Factorial function", r'''
#include <stdio.h>
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}
int main() {
    int result;
    result = factorial(5);
    printf("5! = %d\n", result);
    return 0;
}
''', expected_contains=["5! = 120"])

# 4) Nested loops
test("Nested loops", r'''
#include <stdio.h>
int main() {
    int i, j, sum;
    sum = 0;
    for (i = 1; i <= 3; i++) {
        for (j = 1; j <= 3; j++) {
            sum = sum + i * j;
        }
    }
    printf("Sum: %d\n", sum);
    return 0;
}
''', expected_contains=["Sum: 36"])

# 5) While loop with scanf
test("While with scanf", r'''
#include <stdio.h>
int main() {
    int n, sum, i;
    scanf("%d", &n);
    sum = 0;
    for (i = 1; i <= n; i++) {
        sum = sum + i;
    }
    printf("Sum of 1 to %d is %d\n", n, sum);
    return 0;
}
''', stdin='10', expected_contains=["Sum of 1 to 10 is 55"])

# 6) If-else chain
test("If-else chain", r'''
#include <stdio.h>
int main() {
    int x;
    x = 85;
    if (x >= 90) {
        printf("Grade: A\n");
    } else if (x >= 80) {
        printf("Grade: B\n");
    } else if (x >= 70) {
        printf("Grade: C\n");
    } else {
        printf("Grade: F\n");
    }
    return 0;
}
''', expected_contains=["Grade: B"])

# 7) Multiple printf format specifiers
test("Mixed printf formats", r'''
#include <stdio.h>
int main() {
    int a;
    float f;
    char c;
    a = 42;
    f = 3.14;
    c = 'A';
    printf("int=%d float=%f char=%c\n", a, f, c);
    return 0;
}
''', expected_contains=["int=42", "char=A"])

# 8) String operations
test("String printf", r'''
#include <stdio.h>
int main() {
    printf("Hello, %s! You are %d years old.\n", "World", 25);
    return 0;
}
''', expected_contains=["Hello, World!", "25 years old"])

# 9) Swap using temp
test("Swap values", r'''
#include <stdio.h>
int main() {
    int a, b, temp;
    a = 10;
    b = 20;
    printf("Before: a=%d b=%d\n", a, b);
    temp = a;
    a = b;
    b = temp;
    printf("After: a=%d b=%d\n", a, b);
    return 0;
}
''', expected_contains=["Before: a=10 b=20", "After: a=20 b=10"])

# 10) Arithmetic expressions
test("Complex arithmetic", r'''
#include <stdio.h>
int main() {
    int a, b, c, result;
    a = 10;
    b = 3;
    c = 7;
    result = a + b * c - a / b;
    printf("Result: %d\n", result);
    return 0;
}
''', expected_contains=["Result:"])
