"""Comprehensive C program test -- every loop, control-flow, and expression pattern."""
import sys, os, traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from compiler_pipeline import run_pipeline
from compile_run import TACInterpreter

PASS = FAIL = ERRORS = 0

def test(name, source, stdin='', expect=None, expect_contains=None):
    global PASS, FAIL, ERRORS
    try:
        result = run_pipeline(source)
        errs = result.get('errors', [])
        if errs:
            ERRORS += 1
            print(f"  COMPILE ERROR: {name}")
            for e in errs[:3]:
                print(f"    {e}")
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
        if ok:
            PASS += 1
            print(f"  PASS: {name}")
        else:
            FAIL += 1
            exp_str = repr(expect) if expect else 'contains ' + str(expect_contains)
            print(f"  FAIL: {name}")
            print(f"    got:      {rt['stdout']!r}")
            print(f"    expected: {exp_str}")
            if rt['stderr']:
                print(f"    stderr:   {rt['stderr']!r}")
    except Exception as e:
        ERRORS += 1
        print(f"  ERROR: {name}: {e}")
        traceback.print_exc()

print("=" * 70)
print("COMPREHENSIVE C PROGRAM TEST SUITE")
print("=" * 70)

# -- 1. DO-WHILE LOOPS --
print("\n-- Do-While Loops --")

test("Do-while basic", r'''
#include <stdio.h>
int main() {
    int i = 1;
    do {
        printf("%d ", i);
        i++;
    } while (i <= 5);
    printf("\n");
    return 0;
}
''', expect="1 2 3 4 5 \n")

test("Do-while runs once", r'''
#include <stdio.h>
int main() {
    int x = 100;
    do {
        printf("ran\n");
        x++;
    } while (x < 50);
    return 0;
}
''', expect="ran\n")

test("Do-while sum", r'''
#include <stdio.h>
int main() {
    int n = 5, sum = 0, i = 1;
    do {
        sum = sum + i;
        i++;
    } while (i <= n);
    printf("%d\n", sum);
    return 0;
}
''', expect="15\n")

test("Do-while countdown", r'''
#include <stdio.h>
int main() {
    int i = 3;
    do {
        printf("%d ", i);
        i--;
    } while (i > 0);
    printf("\n");
    return 0;
}
''', expect="3 2 1 \n")

# -- 2. SWITCH-CASE --
print("\n-- Switch-Case --")

test("Switch basic", r'''
#include <stdio.h>
int main() {
    int x = 2;
    switch (x) {
    case 1: printf("one\n"); break;
    case 2: printf("two\n"); break;
    case 3: printf("three\n"); break;
    default: printf("other\n");
    }
    return 0;
}
''', expect="two\n")

test("Switch default", r'''
#include <stdio.h>
int main() {
    int x = 99;
    switch (x) {
    case 1: printf("one\n"); break;
    case 2: printf("two\n"); break;
    default: printf("default\n");
    }
    return 0;
}
''', expect="default\n")

test("Switch char", r'''
#include <stdio.h>
int main() {
    char ch = 'B';
    switch (ch) {
    case 'A': printf("Apple\n"); break;
    case 'B': printf("Banana\n"); break;
    case 'C': printf("Cherry\n"); break;
    default: printf("Unknown\n");
    }
    return 0;
}
''', expect="Banana\n")

test("Switch calculator", r'''
#include <stdio.h>
int main() {
    char op;
    int a, b;
    scanf("%c", &op);
    scanf("%d %d", &a, &b);
    switch (op) {
    case '+': printf("%d\n", a + b); break;
    case '-': printf("%d\n", a - b); break;
    case '*': printf("%d\n", a * b); break;
    case '/': printf("%d\n", a / b); break;
    default: printf("Invalid\n");
    }
    return 0;
}
''', stdin="+ 10 20", expect="30\n")

test("Switch no default", r'''
#include <stdio.h>
int main() {
    int x = 3;
    switch (x) {
    case 1: printf("1\n"); break;
    case 2: printf("2\n"); break;
    case 3: printf("3\n"); break;
    }
    printf("done\n");
    return 0;
}
''', expect="3\ndone\n")

# -- 3. FOR LOOP PATTERNS --
print("\n-- For Loop Patterns --")

test("For sum 1 to 10", r'''
#include <stdio.h>
int main() {
    int i, sum = 0;
    for (i = 1; i <= 10; i++) {
        sum = sum + i;
    }
    printf("%d\n", sum);
    return 0;
}
''', expect="55\n")

test("For nested 3x3", r'''
#include <stdio.h>
int main() {
    int i, j;
    for (i = 1; i <= 3; i++) {
        for (j = 1; j <= 3; j++) {
            printf("%d ", i * j);
        }
        printf("\n");
    }
    return 0;
}
''', expect="1 2 3 \n2 4 6 \n3 6 9 \n")

test("For star pattern", r'''
#include <stdio.h>
int main() {
    int i, j;
    for (i = 1; i <= 4; i++) {
        for (j = 0; j < i; j++) {
            printf("*");
        }
        printf("\n");
    }
    return 0;
}
''', expect="*\n**\n***\n****\n")

test("For backwards", r'''
#include <stdio.h>
int main() {
    int i;
    for (i = 10; i >= 1; i--) {
        printf("%d ", i);
    }
    printf("\n");
    return 0;
}
''', expect="10 9 8 7 6 5 4 3 2 1 \n")

test("For even numbers", r'''
#include <stdio.h>
int main() {
    int i;
    for (i = 0; i <= 10; i++) {
        if (i % 2 == 0)
            printf("%d ", i);
    }
    printf("\n");
    return 0;
}
''', expect="0 2 4 6 8 10 \n")

# -- 4. WHILE LOOP PATTERNS --
print("\n-- While Loop Patterns --")

test("While reverse number", r'''
#include <stdio.h>
int main() {
    int n = 100, rev = 0;
    while (n > 0) {
        rev = rev * 10 + n % 10;
        n = n / 10;
    }
    printf("%d\n", rev);
    return 0;
}
''', expect="1\n")

test("While power of 2", r'''
#include <stdio.h>
int main() {
    int p = 1, i = 0;
    while (i < 8) {
        printf("%d ", p);
        p = p * 2;
        i++;
    }
    printf("\n");
    return 0;
}
''', expect="1 2 4 8 16 32 64 128 \n")

test("While digit extraction", r'''
#include <stdio.h>
int main() {
    int n = 9876, d;
    while (n > 0) {
        d = n % 10;
        printf("%d ", d);
        n = n / 10;
    }
    printf("\n");
    return 0;
}
''', expect="6 7 8 9 \n")

# -- 5. NESTED CONTROL FLOW --
print("\n-- Nested Control Flow --")

test("If inside for", r'''
#include <stdio.h>
int main() {
    int i;
    for (i = 1; i <= 10; i++) {
        if (i % 3 == 0)
            printf("%d ", i);
    }
    printf("\n");
    return 0;
}
''', expect="3 6 9 \n")

test("For inside if", r'''
#include <stdio.h>
int main() {
    int n = 5, i, fact = 1;
    if (n > 0) {
        for (i = 1; i <= n; i++)
            fact = fact * i;
        printf("%d\n", fact);
    } else {
        printf("1\n");
    }
    return 0;
}
''', expect="120\n")

test("While inside while", r'''
#include <stdio.h>
int main() {
    int i = 1, j;
    while (i <= 3) {
        j = 1;
        while (j <= i) {
            printf("%d", j);
            j++;
        }
        printf("\n");
        i++;
    }
    return 0;
}
''', expect="1\n12\n123\n")

test("If-else inside while", r'''
#include <stdio.h>
int main() {
    int i = 1;
    while (i <= 5) {
        if (i % 2 == 0)
            printf("E");
        else
            printf("O");
        i++;
    }
    printf("\n");
    return 0;
}
''', expect="OEOEO\n")

# -- 6. ARRAY OPERATIONS --
print("\n-- Array Operations --")

test("Array linear search", r'''
#include <stdio.h>
int main() {
    int arr[5], i, key, found;
    arr[0] = 10; arr[1] = 20; arr[2] = 30; arr[3] = 40; arr[4] = 50;
    key = 30;
    found = 0;
    for (i = 0; i < 5; i++) {
        if (arr[i] == key) {
            found = 1;
        }
    }
    if (found) printf("Found\n"); else printf("Not found\n");
    return 0;
}
''', expect="Found\n")

test("Array copy", r'''
#include <stdio.h>
int main() {
    int a[3], b[3], i;
    a[0] = 1; a[1] = 2; a[2] = 3;
    for (i = 0; i < 3; i++) b[i] = a[i];
    for (i = 0; i < 3; i++) printf("%d ", b[i]);
    printf("\n");
    return 0;
}
''', expect="1 2 3 \n")

test("Array min and max", r'''
#include <stdio.h>
int main() {
    int arr[5], i, mn, mx;
    arr[0]=7; arr[1]=2; arr[2]=9; arr[3]=1; arr[4]=5;
    mn = arr[0]; mx = arr[0];
    for (i = 1; i < 5; i++) {
        if (arr[i] < mn) mn = arr[i];
        if (arr[i] > mx) mx = arr[i];
    }
    printf("Min=%d Max=%d\n", mn, mx);
    return 0;
}
''', expect="Min=1 Max=9\n")

test("Selection sort", r'''
#include <stdio.h>
int main() {
    int arr[5], i, j, min_idx, temp;
    arr[0]=29; arr[1]=10; arr[2]=14; arr[3]=37; arr[4]=13;
    for (i = 0; i < 4; i++) {
        min_idx = i;
        for (j = i + 1; j < 5; j++) {
            if (arr[j] < arr[min_idx])
                min_idx = j;
        }
        temp = arr[i]; arr[i] = arr[min_idx]; arr[min_idx] = temp;
    }
    for (i = 0; i < 5; i++) printf("%d ", arr[i]);
    printf("\n");
    return 0;
}
''', expect="10 13 14 29 37 \n")

test("Array average", r'''
#include <stdio.h>
int main() {
    int arr[4], i, sum = 0;
    arr[0] = 10; arr[1] = 20; arr[2] = 30; arr[3] = 40;
    for (i = 0; i < 4; i++) sum = sum + arr[i];
    printf("%d\n", sum / 4);
    return 0;
}
''', expect="25\n")

# -- 7. FUNCTIONS --
print("\n-- Functions --")

test("Void function", r'''
#include <stdio.h>
void greet() {
    printf("Hello!\n");
}
int main() {
    greet();
    return 0;
}
''', expect="Hello!\n")

test("Function with loop", r'''
#include <stdio.h>
int sum_to_n(int n) {
    int i, s = 0;
    for (i = 1; i <= n; i++) s = s + i;
    return s;
}
int main() {
    printf("%d\n", sum_to_n(10));
    return 0;
}
''', expect="55\n")

test("Recursive fibonacci", r'''
#include <stdio.h>
int fib(int n) {
    if (n <= 0) return 0;
    if (n == 1) return 1;
    return fib(n - 1) + fib(n - 2);
}
int main() {
    printf("%d\n", fib(10));
    return 0;
}
''', expect="55\n")

test("Multiple return paths", r'''
#include <stdio.h>
int abs_val(int x) {
    if (x < 0) return 0 - x;
    return x;
}
int main() {
    printf("%d %d %d\n", abs_val(5), abs_val(-3), abs_val(0));
    return 0;
}
''', expect="5 3 0\n")

test("Function calling function", r'''
#include <stdio.h>
int double_it(int x) { return x * 2; }
int quad(int x) { return double_it(double_it(x)); }
int main() {
    printf("%d\n", quad(3));
    return 0;
}
''', expect="12\n")

# -- 8. COMPOUND EXPRESSIONS --
print("\n-- Compound Expressions --")

test("Chained assignment", r'''
#include <stdio.h>
int main() {
    int a, b, c;
    a = 10;
    b = a + 5;
    c = a + b;
    printf("%d\n", c);
    return 0;
}
''', expect="25\n")

test("Expression in printf", r'''
#include <stdio.h>
int main() {
    int x = 7;
    printf("%d %d %d\n", x + 1, x * 2, x - 3);
    return 0;
}
''', expect="8 14 4\n")

test("Complex boolean", r'''
#include <stdio.h>
int main() {
    int a = 5, b = 10, c = 15;
    if (a < b && b < c) printf("asc\n");
    if (a > 0 || b < 0) printf("pos\n");
    return 0;
}
''', expect="asc\npos\n")

# -- 9. SCANF PATTERNS --
print("\n-- Scanf Patterns --")

test("Scanf multiple types", r'''
#include <stdio.h>
int main() {
    int a;
    float b;
    scanf("%d", &a);
    scanf("%f", &b);
    printf("int=%d float=%f\n", a, b);
    return 0;
}
''', stdin="42 3.14", expect="int=42 float=3.140000\n")

test("Scanf in loop", r'''
#include <stdio.h>
int main() {
    int i, n, sum = 0;
    scanf("%d", &n);
    for (i = 0; i < n; i++) {
        int x;
        scanf("%d", &x);
        sum = sum + x;
    }
    printf("%d\n", sum);
    return 0;
}
''', stdin="3 10 20 30", expect="60\n")

# -- 10. CLASSIC ALGORITHMS --
print("\n-- Classic Algorithms --")

test("LCM", r'''
#include <stdio.h>
int gcd(int a, int b) {
    while (b != 0) { int t = b; b = a % b; a = t; }
    return a;
}
int main() {
    int a = 12, b = 18;
    int lcm = a / gcd(a, b) * b;
    printf("%d\n", lcm);
    return 0;
}
''', expect="36\n")

test("Armstrong 153", r'''
#include <stdio.h>
int main() {
    int n = 153, orig = 153, sum = 0;
    while (n > 0) {
        int d = n % 10;
        sum = sum + d * d * d;
        n = n / 10;
    }
    if (sum == orig) printf("yes\n"); else printf("no\n");
    return 0;
}
''', expect="yes\n")

test("Matrix multiply 2x2", r'''
#include <stdio.h>
int main() {
    int a[4], b[4], c[4];
    a[0]=1; a[1]=2; a[2]=3; a[3]=4;
    b[0]=5; b[1]=6; b[2]=7; b[3]=8;
    c[0] = a[0]*b[0] + a[1]*b[2];
    c[1] = a[0]*b[1] + a[1]*b[3];
    c[2] = a[2]*b[0] + a[3]*b[2];
    c[3] = a[2]*b[1] + a[3]*b[3];
    printf("%d %d %d %d\n", c[0], c[1], c[2], c[3]);
    return 0;
}
''', expect="19 22 43 50\n")

test("Insertion sort", r'''
#include <stdio.h>
int main() {
    int arr[5], i, j, key;
    arr[0]=5; arr[1]=3; arr[2]=4; arr[3]=1; arr[4]=2;
    for (i = 1; i < 5; i++) {
        key = arr[i];
        j = i - 1;
        while (j >= 0 && arr[j] > key) {
            arr[j + 1] = arr[j];
            j--;
        }
        arr[j + 1] = key;
    }
    for (i = 0; i < 5; i++) printf("%d ", arr[i]);
    printf("\n");
    return 0;
}
''', expect="1 2 3 4 5 \n")

test("Count occurrences", r'''
#include <stdio.h>
int main() {
    int arr[8], i, count = 0, target = 3;
    arr[0]=1; arr[1]=3; arr[2]=5; arr[3]=3;
    arr[4]=3; arr[5]=7; arr[6]=3; arr[7]=9;
    for (i = 0; i < 8; i++) {
        if (arr[i] == target) count++;
    }
    printf("%d\n", count);
    return 0;
}
''', expect="4\n")

# -- 11. MULTIPLE I/O --
print("\n-- Multiple I/O --")

test("Menu-driven", r'''
#include <stdio.h>
int main() {
    int choice, a, b;
    scanf("%d", &choice);
    scanf("%d %d", &a, &b);
    if (choice == 1) printf("Sum: %d\n", a + b);
    else if (choice == 2) printf("Diff: %d\n", a - b);
    else if (choice == 3) printf("Prod: %d\n", a * b);
    else printf("Invalid\n");
    return 0;
}
''', stdin="3 6 7", expect="Prod: 42\n")

test("Multiple printfs", r'''
#include <stdio.h>
int main() {
    printf("Line 1\n");
    printf("Line 2\n");
    printf("Line 3\n");
    return 0;
}
''', expect="Line 1\nLine 2\nLine 3\n")

# -- 12. EDGE CASES --
print("\n-- Edge Cases --")

test("Zero iter for", r'''
#include <stdio.h>
int main() {
    int i;
    for (i = 10; i < 5; i++) printf("nope");
    printf("done\n");
    return 0;
}
''', expect="done\n")

test("Zero iter while", r'''
#include <stdio.h>
int main() {
    int i = 10;
    while (i < 5) { printf("nope"); i++; }
    printf("done\n");
    return 0;
}
''', expect="done\n")

test("Single element array", r'''
#include <stdio.h>
int main() {
    int a[1];
    a[0] = 42;
    printf("%d\n", a[0]);
    return 0;
}
''', expect="42\n")

test("Large numbers", r'''
#include <stdio.h>
int main() {
    int a = 100000, b = 200000;
    printf("%d\n", a + b);
    return 0;
}
''', expect="300000\n")

test("Reassign many times", r'''
#include <stdio.h>
int main() {
    int x = 1;
    x = x + 1;
    x = x * 3;
    x = x - 2;
    x = x + 10;
    printf("%d\n", x);
    return 0;
}
''', expect="14\n")

test("Deep nested if-else", r'''
#include <stdio.h>
int main() {
    int x = 50;
    if (x > 90) printf("A\n");
    else if (x > 80) printf("B\n");
    else if (x > 70) printf("C\n");
    else if (x > 60) printf("D\n");
    else printf("F\n");
    return 0;
}
''', expect="F\n")

test("Compound condition", r'''
#include <stdio.h>
int main() {
    int a = 15;
    if (a >= 10 && a <= 20) printf("in range\n");
    return 0;
}
''', expect="in range\n")

test("Multiple arrays", r'''
#include <stdio.h>
int main() {
    int a[3], b[3], c[3], i;
    for (i = 0; i < 3; i++) { a[i] = i + 1; b[i] = (i + 1) * 10; }
    for (i = 0; i < 3; i++) c[i] = a[i] + b[i];
    for (i = 0; i < 3; i++) printf("%d ", c[i]);
    printf("\n");
    return 0;
}
''', expect="11 22 33 \n")

# -- 13. REAL-WORLD PROGRAMS --
print("\n-- Real-World Programs --")

test("Temperature converter", r'''
#include <stdio.h>
int main() {
    float celsius;
    scanf("%f", &celsius);
    float fahrenheit = celsius * 9 / 5 + 32;
    printf("%.2f\n", fahrenheit);
    return 0;
}
''', stdin="100", expect="212.00\n")

test("Simple interest", r'''
#include <stdio.h>
int main() {
    int p = 1000, r = 5, t = 2;
    int si = p * r * t / 100;
    printf("SI = %d\n", si);
    return 0;
}
''', expect="SI = 100\n")

test("Leap year", r'''
#include <stdio.h>
int main() {
    int year = 2024;
    if (year % 400 == 0) printf("Leap\n");
    else if (year % 100 == 0) printf("Not Leap\n");
    else if (year % 4 == 0) printf("Leap\n");
    else printf("Not Leap\n");
    return 0;
}
''', expect="Leap\n")

test("Sum from user array", r'''
#include <stdio.h>
int main() {
    int n, i, sum = 0;
    int arr[10];
    scanf("%d", &n);
    for (i = 0; i < n; i++) scanf("%d", &arr[i]);
    for (i = 0; i < n; i++) sum = sum + arr[i];
    printf("Sum = %d\n", sum);
    return 0;
}
''', stdin="5 10 20 30 40 50", expect="Sum = 150\n")

test("Number pattern", r'''
#include <stdio.h>
int main() {
    int i, j;
    for (i = 1; i <= 4; i++) {
        for (j = 1; j <= i; j++) printf("%d", j);
        printf("\n");
    }
    return 0;
}
''', expect="1\n12\n123\n1234\n")

# -- 14. COMBINED FEATURES --
print("\n-- Combined Features --")

test("GCD + LCM", r'''
#include <stdio.h>
int gcd(int a, int b) {
    while (b != 0) { int t = b; b = a % b; a = t; }
    return a;
}
int main() {
    int a = 24, b = 36;
    int g = gcd(a, b);
    int l = a / g * b;
    printf("GCD=%d LCM=%d\n", g, l);
    return 0;
}
''', expect="GCD=12 LCM=72\n")

test("Prime sieve", r'''
#include <stdio.h>
int main() {
    int i, j, is_prime;
    for (i = 2; i <= 20; i++) {
        is_prime = 1;
        for (j = 2; j < i; j++) {
            if (i % j == 0) { is_prime = 0; }
        }
        if (is_prime) printf("%d ", i);
    }
    printf("\n");
    return 0;
}
''', expect="2 3 5 7 11 13 17 19 \n")

test("Swap without temp", r'''
#include <stdio.h>
int main() {
    int a = 10, b = 20;
    a = a + b;
    b = a - b;
    a = a - b;
    printf("%d %d\n", a, b);
    return 0;
}
''', expect="20 10\n")

test("Count vowels (numeric)", r'''
#include <stdio.h>
int main() {
    int arr[5], i, count = 0;
    arr[0] = 97; arr[1] = 98; arr[2] = 101; arr[3] = 105; arr[4] = 120;
    for (i = 0; i < 5; i++) {
        if (arr[i]==97 || arr[i]==101 || arr[i]==105 || arr[i]==111 || arr[i]==117)
            count++;
    }
    printf("%d\n", count);
    return 0;
}
''', expect="3\n")

print("\n" + "=" * 70)
print(f"RESULTS: {PASS} passed, {FAIL} failed, {ERRORS} errors")
print(f"TOTAL:   {PASS + FAIL + ERRORS} tests")
print("=" * 70)
