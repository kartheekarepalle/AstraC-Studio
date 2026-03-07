import sys; sys.path.insert(0, 'backend/app/services'); sys.path.insert(0, 'api')
from compiler_pipeline import run_pipeline
from compile_run import TACInterpreter

def test(name, code):
    r = run_pipeline(code)
    tac = r.get('optimized_ir') or r.get('ir') or []
    interp = TACInterpreter(tac)
    result = interp.run()
    print(f"--- {name} ---")
    print(f"  stdout: {repr(result['stdout'])}")
    if result['stderr']:
        print(f"  stderr: {result['stderr']}")
    print(f"  exit: {result['exit_code']}")
    print()

code = r'''
int main(){
    int x = 3 + 4;
    printf("%d\n", x);
    return 0;
}
'''
test("simple add + printf", code)

print()
print('OptIR:')
for line in r['optimized_ir']: print('  ', repr(line))

print('\n--- Test 2: loop ---')
code2 = r'''
int main(){
    int i;
    int sum = 0;
    for(i = 0; i < 5; i++){
        sum = sum + i;
    }
    printf("sum=%d\n", sum);
    return 0;
}
'''
r2 = run_pipeline(code2)
print('IR:')
for line in r2['ir']: print('  ', repr(line))

print('\n--- Test 3: if/else ---')
code3 = r'''
int main(){
    int x = 10;
    if(x > 5){
        printf("big\n");
    } else {
        printf("small\n");
    }
    return 0;
}
'''
r3 = run_pipeline(code3)
print('IR:')
for line in r3['ir']: print('  ', repr(line))

print('\n--- Test 4: factorial ---')
code4 = """int factorial(int n){
    if(n <= 1){ return 1; }
    return n * factorial(n - 1);
}
int main(){
    int r = factorial(5);
    printf("Result: %d\\n", r);
    return 0;
}"""
r4 = run_pipeline(code4)
print('IR:')
for line in r4['ir']: print('  ', repr(line))
