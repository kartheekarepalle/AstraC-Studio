"""Test the new Copy Propagation + DCE optimizations."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'app', 'services'))
from compiler_pipeline import phase_lexical, phase_intermediate, phase_optimization

def test_program(label, code):
    print(f"\n{'='*60}")
    print(f"  TEST: {label}")
    print(f"{'='*60}")
    lex = phase_lexical(code)
    ir = phase_intermediate(lex['tokens'])
    print("\n--- Original TAC ---")
    for line in ir['ir']:
        print(f"  {line}")

    opt = phase_optimization(ir['ir'])
    print(f"\n--- Optimized TAC ---")
    for line in opt['optimized_ir']:
        print(f"  {line}")

    print(f"\n--- Changes ({len(opt['changes'])}) ---")
    for c in opt['changes']:
        print(f"  [{c['rule']}]  {c['original']}  -->  {c['optimized']}")

    if not opt['changes']:
        print("  (none)")
    return len(opt['changes'])


# Test 1: Simple scanf program (previously showed 0 optimizations)
c1 = test_program("scanf + arithmetic (no constants)", """
int main() {
    int a, b, sum;
    scanf("%d %d", &a, &b);
    sum = a + b;
    printf("Sum = %d", sum);
    return 0;
}
""")

# Test 2: Loop with array (previously showed 0 optimizations)
c2 = test_program("Loop with array ops", """
int main() {
    int arr[10], i, sum;
    sum = 0;
    for (i = 0; i < 10; i++) {
        scanf("%d", &arr[i]);
        sum = sum + arr[i];
    }
    printf("Sum = %d", sum);
    return 0;
}
""")

# Test 3: Max/min program (previously showed 0 optimizations)
c3 = test_program("Max/min finder", """
int main() {
    int arr[5], i, max, min;
    for (i = 0; i < 5; i++) {
        scanf("%d", &arr[i]);
    }
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
    printf("Max=%d Min=%d", max, min);
    return 0;
}
""")

# Test 4: Constants + expressions (should trigger both old and new opts)
c4 = test_program("Constants + expressions", """
int main() {
    int x, y, z;
    x = 3 + 4;
    y = x * 2;
    z = x + y + 0;
    printf("%d", z);
    return 0;
}
""")

# Test 5: if-else with arithmetic
c5 = test_program("if-else with arithmetic", """
int main() {
    int a, b, max;
    scanf("%d %d", &a, &b);
    if (a > b) {
        max = a;
    } else {
        max = b;
    }
    int result;
    result = max * 2 + 1;
    printf("%d", result);
    return 0;
}
""")

print(f"\n\n{'='*60}")
print(f"  SUMMARY")
print(f"{'='*60}")
print(f"  Test 1 (scanf+arith):     {c1} optimizations")
print(f"  Test 2 (loop+array):      {c2} optimizations")
print(f"  Test 3 (max/min):         {c3} optimizations")
print(f"  Test 4 (constants):       {c4} optimizations")
print(f"  Test 5 (if-else+arith):   {c5} optimizations")
total_zero = sum(1 for c in [c1,c2,c3,c4,c5] if c == 0)
print(f"\n  Programs with 0 opts:     {total_zero}/5")
