"""Exhaustive test suite — find ALL remaining interpreter/pipeline bugs."""
import sys, os, traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from compiler_pipeline import run_pipeline
from compile_run import TACInterpreter

PASS = 0
FAIL = 0
ERRORS = 0

def test(name, source, stdin='', expect=None, expect_contains=None, expect_exit=0):
    global PASS, FAIL, ERRORS
    try:
        result = run_pipeline(source)
        errs = result.get('errors', [])
        if errs:
            print(f"  COMPILE ERROR: {errs}")
            ERRORS += 1
            return
        tac = result.get('optimized_ir') or result.get('ir') or []
        interp = TACInterpreter(tac, stdin_text=stdin)
        rt = interp.run()
        ok = True
        if expect is not None and rt['stdout'] != expect:
            ok = False
        if expect_contains:
            for s in expect_contains:
                if s not in rt['stdout']:
                    ok = False
        if rt['exit_code'] != expect_exit and expect_exit is not None:
            ok = False
        if ok:
            PASS += 1
            print(f"  PASS: {name}")
        else:
            FAIL += 1
            print(f"  FAIL: {name}")
            print(f"    stdout:   {rt['stdout']!r}")
            exp_str = repr(expect) if expect else 'contains ' + str(expect_contains)
            print(f"    expected: {exp_str}")
            if rt['stderr']:
                print(f"    stderr:   {rt['stderr']!r}")
            print(f"    TAC:")
            for l in tac:
                print(f"      {l}")
    except Exception as e:
        ERRORS += 1
        print(f"  ERROR: {name}: {e}")
        traceback.print_exc()

print("=" * 70)
print("EXHAUSTIVE TEST SUITE")
print("=" * 70)

# ── 1. Basic I/O ──
test("Hello World", r'''
#include <stdio.h>
int main() { printf("Hello, World!\n"); return 0; }
''', expect="Hello, World!\n")

test("Printf int", r'''
#include <stdio.h>
int main() { printf("%d\n", 42); return 0; }
''', expect="42\n")

test("Printf float", r'''
#include <stdio.h>
int main() { printf("%.6f\n", 3.14); return 0; }
''', expect="3.140000\n")

test("Printf char", r'''
#include <stdio.h>
int main() { char c = 'A'; printf("%c\n", c); return 0; }
''', expect="A\n")

test("Printf string", r'''
#include <stdio.h>
int main() { printf("Name: %s\n", "Alice"); return 0; }
''', expect="Name: Alice\n")

test("Printf multiple args", r'''
#include <stdio.h>
int main() { printf("%d + %d = %d\n", 3, 4, 7); return 0; }
''', expect="3 + 4 = 7\n")

test("Printf no newline", r'''
#include <stdio.h>
int main() { printf("abc"); printf("def"); return 0; }
''', expect="abcdef")

# ── 2. Scanf ──
test("Scanf int", r'''
#include <stdio.h>
int main() { int x; scanf("%d", &x); printf("%d\n", x); return 0; }
''', stdin="99", expect="99\n")

test("Scanf two ints", r'''
#include <stdio.h>
int main() {
    int a, b;
    scanf("%d %d", &a, &b);
    printf("Sum: %d\n", a + b);
    return 0;
}
''', stdin="10 20", expect="Sum: 30\n")

test("Scanf float", r'''
#include <stdio.h>
int main() { float x; scanf("%f", &x); printf("%f\n", x); return 0; }
''', stdin="2.5", expect="2.500000\n")

# ── 3. Arithmetic ──
test("Add", r'''
#include <stdio.h>
int main() { int a = 5, b = 3; printf("%d\n", a + b); return 0; }
''', expect="8\n")

test("Subtract", r'''
#include <stdio.h>
int main() { int a = 10, b = 4; printf("%d\n", a - b); return 0; }
''', expect="6\n")

test("Multiply", r'''
#include <stdio.h>
int main() { int a = 6, b = 7; printf("%d\n", a * b); return 0; }
''', expect="42\n")

test("Divide", r'''
#include <stdio.h>
int main() { int a = 15, b = 4; printf("%d\n", a / b); return 0; }
''', expect="3\n")

test("Modulo", r'''
#include <stdio.h>
int main() { int a = 17, b = 5; printf("%d\n", a % b); return 0; }
''', expect="2\n")

test("Negative number", r'''
#include <stdio.h>
int main() { int x = -10; printf("%d\n", x); return 0; }
''', expect="-10\n")

test("Mixed precedence", r'''
#include <stdio.h>
int main() { printf("%d\n", 2 + 3 * 4); return 0; }
''', expect="14\n")

test("Complex expr", r'''
#include <stdio.h>
int main() { int a=10,b=3,c=7; int r = a + b * c; printf("%d\n", r); return 0; }
''', expect="31\n")

# ── 4. Variables and assignments ──
test("Multi assignment", r'''
#include <stdio.h>
int main() {
    int a, b, c;
    a = 1; b = 2; c = 3;
    printf("%d %d %d\n", a, b, c);
    return 0;
}
''', expect="1 2 3\n")

test("Swap", r'''
#include <stdio.h>
int main() {
    int a = 10, b = 20, temp;
    temp = a; a = b; b = temp;
    printf("%d %d\n", a, b);
    return 0;
}
''', expect="20 10\n")

test("Increment", r'''
#include <stdio.h>
int main() { int x = 5; x++; printf("%d\n", x); return 0; }
''', expect_contains=["6"])

test("Decrement", r'''
#include <stdio.h>
int main() { int x = 5; x--; printf("%d\n", x); return 0; }
''', expect_contains=["4"])

# ── 5. Control flow: if/else ──
test("If true", r'''
#include <stdio.h>
int main() { int x = 10; if (x > 5) printf("yes\n"); return 0; }
''', expect="yes\n")

test("If false", r'''
#include <stdio.h>
int main() { int x = 3; if (x > 5) printf("yes\n"); printf("done\n"); return 0; }
''', expect="done\n")

test("If-else", r'''
#include <stdio.h>
int main() {
    int x = 3;
    if (x > 5) { printf("big\n"); } else { printf("small\n"); }
    return 0;
}
''', expect="small\n")

test("If-else if-else", r'''
#include <stdio.h>
int main() {
    int x = 75;
    if (x >= 90) printf("A\n");
    else if (x >= 80) printf("B\n");
    else if (x >= 70) printf("C\n");
    else printf("F\n");
    return 0;
}
''', expect="C\n")

test("Nested if", r'''
#include <stdio.h>
int main() {
    int a = 5, b = 10;
    if (a > 0) {
        if (b > 5) { printf("both\n"); }
    }
    return 0;
}
''', expect="both\n")

# ── 6. Loops ──
test("While loop", r'''
#include <stdio.h>
int main() {
    int i = 0;
    while (i < 5) { printf("%d ", i); i++; }
    printf("\n");
    return 0;
}
''', expect="0 1 2 3 4 \n")

test("For loop", r'''
#include <stdio.h>
int main() {
    int i;
    for (i = 1; i <= 5; i++) { printf("%d ", i); }
    printf("\n");
    return 0;
}
''', expect="1 2 3 4 5 \n")

test("For countdown", r'''
#include <stdio.h>
int main() {
    int i;
    for (i = 5; i > 0; i--) printf("%d ", i);
    printf("\n");
    return 0;
}
''', expect="5 4 3 2 1 \n")

test("Nested loops", r'''
#include <stdio.h>
int main() {
    int i, j, sum = 0;
    for (i = 1; i <= 3; i++)
        for (j = 1; j <= 3; j++)
            sum = sum + i * j;
    printf("%d\n", sum);
    return 0;
}
''', expect="36\n")

test("Sum 1 to N", r'''
#include <stdio.h>
int main() {
    int n, i, sum = 0;
    scanf("%d", &n);
    for (i = 1; i <= n; i++) sum = sum + i;
    printf("%d\n", sum);
    return 0;
}
''', stdin="100", expect="5050\n")

# ── 7. Arrays ──
test("Array init and read", r'''
#include <stdio.h>
int main() {
    int arr[3];
    arr[0] = 10; arr[1] = 20; arr[2] = 30;
    printf("%d %d %d\n", arr[0], arr[1], arr[2]);
    return 0;
}
''', expect="10 20 30\n")

test("Array max", r'''
#include <stdio.h>
int main() {
    int arr[5], i, max;
    arr[0]=10; arr[1]=25; arr[2]=5; arr[3]=40; arr[4]=15;
    max = arr[0];
    for (i = 1; i < 5; i++) if (arr[i] > max) max = arr[i];
    printf("Max: %d\n", max);
    return 0;
}
''', expect="Max: 40\n")

test("Array sum", r'''
#include <stdio.h>
int main() {
    int arr[5], i, sum = 0;
    arr[0]=1; arr[1]=2; arr[2]=3; arr[3]=4; arr[4]=5;
    for (i = 0; i < 5; i++) sum = sum + arr[i];
    printf("Sum: %d\n", sum);
    return 0;
}
''', expect="Sum: 15\n")

test("Array scanf", r'''
#include <stdio.h>
int main() {
    int arr[3], i, sum = 0;
    for (i = 0; i < 3; i++) scanf("%d", &arr[i]);
    for (i = 0; i < 3; i++) sum = sum + arr[i];
    printf("%d\n", sum);
    return 0;
}
''', stdin="10 20 30", expect="60\n")

test("Bubble sort", r'''
#include <stdio.h>
int main() {
    int arr[5], i, j, temp;
    arr[0]=64; arr[1]=34; arr[2]=25; arr[3]=12; arr[4]=22;
    for (i = 0; i < 4; i++)
        for (j = 0; j < 4; j++)
            if (arr[j] > arr[j+1]) {
                temp = arr[j]; arr[j] = arr[j+1]; arr[j+1] = temp;
            }
    for (i = 0; i < 5; i++) printf("%d ", arr[i]);
    printf("\n");
    return 0;
}
''', expect="12 22 25 34 64 \n")

# ── 8. Functions ──
test("Function call", r'''
#include <stdio.h>
int add(int a, int b) { return a + b; }
int main() { printf("%d\n", add(3, 4)); return 0; }
''', expect="7\n")

test("Factorial recursive", r'''
#include <stdio.h>
int fact(int n) { if (n <= 1) return 1; return n * fact(n - 1); }
int main() { printf("%d\n", fact(5)); return 0; }
''', expect="120\n")

test("Power function", r'''
#include <stdio.h>
int power(int base, int exp) {
    int r = 1, i;
    for (i = 0; i < exp; i++) r = r * base;
    return r;
}
int main() { printf("%d\n", power(2, 10)); return 0; }
''', expect="1024\n")

test("GCD", r'''
#include <stdio.h>
int gcd(int a, int b) {
    while (b != 0) { int t = b; b = a % b; a = t; }
    return a;
}
int main() { printf("%d\n", gcd(48, 18)); return 0; }
''', expect="6\n")

test("Multiple functions", r'''
#include <stdio.h>
int square(int x) { return x * x; }
int cube(int x) { return x * x * x; }
int main() {
    printf("%d %d\n", square(5), cube(3));
    return 0;
}
''', expect="25 27\n")

# ── 9. Comparison operators ──
test("Equal", r'''
#include <stdio.h>
int main() { int a=5,b=5; if(a==b) printf("eq\n"); return 0; }
''', expect="eq\n")

test("Not equal", r'''
#include <stdio.h>
int main() { int a=5,b=6; if(a!=b) printf("ne\n"); return 0; }
''', expect="ne\n")

test("Less than", r'''
#include <stdio.h>
int main() { int a=3,b=5; if(a<b) printf("lt\n"); return 0; }
''', expect="lt\n")

test("Greater equal", r'''
#include <stdio.h>
int main() { int a=5,b=5; if(a>=b) printf("ge\n"); return 0; }
''', expect="ge\n")

# ── 10. Logical operators ──
test("AND true", r'''
#include <stdio.h>
int main() { int a=1,b=1; if(a&&b) printf("yes\n"); return 0; }
''', expect="yes\n")

test("OR true", r'''
#include <stdio.h>
int main() { int a=0,b=1; if(a||b) printf("yes\n"); return 0; }
''', expect="yes\n")

test("NOT", r'''
#include <stdio.h>
int main() { int a=0; if(!a) printf("yes\n"); return 0; }
''', expect="yes\n")

# ── 11. Edge cases ──
test("Empty main", r'''
#include <stdio.h>
int main() { return 0; }
''', expect="")

test("Large loop", r'''
#include <stdio.h>
int main() {
    int i, sum = 0;
    for (i = 1; i <= 1000; i++) sum = sum + i;
    printf("%d\n", sum);
    return 0;
}
''', expect="500500\n")

test("Fibonacci", r'''
#include <stdio.h>
int main() {
    int a=0,b=1,c,i;
    for (i=0; i<10; i++) {
        printf("%d ", a);
        c = a + b; a = b; b = c;
    }
    printf("\n");
    return 0;
}
''', expect="0 1 1 2 3 5 8 13 21 34 \n")

test("Prime check", r'''
#include <stdio.h>
int main() {
    int n=17, i, is_prime=1;
    for (i=2; i<n; i++) if(n%i==0) is_prime=0;
    if (is_prime) printf("prime\n"); else printf("not prime\n");
    return 0;
}
''', expect="prime\n")

test("Absolute value", r'''
#include <stdio.h>
int main() {
    int x = -42;
    if (x < 0) x = 0 - x;
    printf("%d\n", x);
    return 0;
}
''', expect="42\n")

test("Multiplication table", r'''
#include <stdio.h>
int main() {
    int i;
    for (i=1; i<=5; i++) printf("5*%d=%d\n", i, 5*i);
    return 0;
}
''', expect="5*1=5\n5*2=10\n5*3=15\n5*4=20\n5*5=25\n")

test("Even odd", r'''
#include <stdio.h>
int main() {
    int n;
    scanf("%d", &n);
    if (n % 2 == 0) printf("even\n"); else printf("odd\n");
    return 0;
}
''', stdin="7", expect="odd\n")

test("Reverse array", r'''
#include <stdio.h>
int main() {
    int arr[5], i, temp;
    arr[0]=1; arr[1]=2; arr[2]=3; arr[3]=4; arr[4]=5;
    for (i=0; i<2; i++) {
        temp = arr[i]; arr[i] = arr[4-i]; arr[4-i] = temp;
    }
    for (i=0; i<5; i++) printf("%d ", arr[i]);
    printf("\n");
    return 0;
}
''', expect="5 4 3 2 1 \n")

test("Count digits", r'''
#include <stdio.h>
int main() {
    int n = 12345, count = 0;
    while (n > 0) { count++; n = n / 10; }
    printf("%d\n", count);
    return 0;
}
''', expect="5\n")

test("Sum of digits", r'''
#include <stdio.h>
int main() {
    int n = 12345, sum = 0;
    while (n > 0) { sum = sum + n % 10; n = n / 10; }
    printf("%d\n", sum);
    return 0;
}
''', expect="15\n")

test("Palindrome check", r'''
#include <stdio.h>
int main() {
    int n = 121, orig = 121, rev = 0;
    while (n > 0) { rev = rev * 10 + n % 10; n = n / 10; }
    if (rev == orig) printf("palindrome\n"); else printf("not palindrome\n");
    return 0;
}
''', expect="palindrome\n")

test("Two functions calling each other pattern", r'''
#include <stdio.h>
int max(int a, int b) { if (a > b) return a; return b; }
int min(int a, int b) { if (a < b) return a; return b; }
int main() {
    printf("max=%d min=%d\n", max(10,20), min(10,20));
    return 0;
}
''', expect="max=20 min=10\n")

print("\n" + "=" * 70)
print(f"RESULTS: {PASS} passed, {FAIL} failed, {ERRORS} errors")
print("=" * 70)
