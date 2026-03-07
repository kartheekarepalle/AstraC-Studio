"""Additional edge case tests."""
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
    for l in tac:
        print(f"    {l}")
    interp = TACInterpreter(tac, stdin_text=stdin)
    rt = interp.run()
    print(f"  stdout: {rt['stdout']!r}")
    if rt['stderr']:
        print(f"  stderr: {rt['stderr']!r}")
    if expected_contains:
        for exp in expected_contains:
            if exp in rt['stdout']:
                print(f"  PASS: contains {exp!r}")
            else:
                print(f"  FAIL: missing {exp!r}")

# 1) Array sum with scanf
test("Array sum with scanf", r'''
#include <stdio.h>
int main() {
    int arr[5], i, sum;
    sum = 0;
    for (i = 0; i < 5; i++) {
        scanf("%d", &arr[i]);
    }
    for (i = 0; i < 5; i++) {
        sum = sum + arr[i];
    }
    printf("Sum = %d\n", sum);
    return 0;
}
''', stdin='10 20 30 40 50', expected_contains=["Sum = 150"])

# 2) Bubble sort
test("Bubble sort", r'''
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
''', expected_contains=["12 22 25 34 64"])

# 3) Power function
test("Power function", r'''
#include <stdio.h>
int power(int base, int exp) {
    int result;
    result = 1;
    int i;
    for (i = 0; i < exp; i++) {
        result = result * base;
    }
    return result;
}
int main() {
    int r;
    r = power(2, 10);
    printf("2^10 = %d\n", r);
    return 0;
}
''', expected_contains=["2^10 = 1024"])

# 4) GCD
test("GCD", r'''
#include <stdio.h>
int gcd(int a, int b) {
    while (b != 0) {
        int temp;
        temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}
int main() {
    int result;
    result = gcd(48, 18);
    printf("GCD of 48 and 18 is %d\n", result);
    return 0;
}
''', expected_contains=["GCD of 48 and 18 is 6"])

# 5) Prime check
test("Prime check", r'''
#include <stdio.h>
int main() {
    int n, i, is_prime;
    n = 17;
    is_prime = 1;
    for (i = 2; i < n; i++) {
        if (n % i == 0) {
            is_prime = 0;
        }
    }
    if (is_prime == 1) {
        printf("%d is prime\n", n);
    } else {
        printf("%d is not prime\n", n);
    }
    return 0;
}
''', expected_contains=["17 is prime"])

# 6) Multiple return values via printf
test("Multiplication table", r'''
#include <stdio.h>
int main() {
    int i;
    for (i = 1; i <= 5; i++) {
        printf("5 x %d = %d\n", i, 5 * i);
    }
    return 0;
}
''', expected_contains=["5 x 1 = 5", "5 x 3 = 15", "5 x 5 = 25"])

# 7) Ternary-like with nested if
test("Absolute value", r'''
#include <stdio.h>
int main() {
    int x, abs;
    x = -42;
    if (x < 0) {
        abs = 0 - x;
    } else {
        abs = x;
    }
    printf("Absolute value of %d is %d\n", x, abs);
    return 0;
}
''', expected_contains=["Absolute value of -42 is 42"])

# 8) String output
test("Multiple strings", r'''
#include <stdio.h>
int main() {
    printf("Name: %s\n", "Alice");
    printf("Age: %d\n", 30);
    printf("City: %s\n", "NYC");
    return 0;
}
''', expected_contains=["Name: Alice", "Age: 30", "City: NYC"])
