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

test("simple add + printf", r'''
int main(){
    int x = 3 + 4;
    printf("%d\n", x);
    return 0;
}
''')

test("loop", r'''
int main(){
    int i;
    int sum = 0;
    for(i = 0; i < 5; i++){
        sum = sum + i;
    }
    printf("sum=%d\n", sum);
    return 0;
}
''')

test("if/else", r'''
int main(){
    int x = 10;
    if(x > 5){
        printf("big\n");
    } else {
        printf("small\n");
    }
    return 0;
}
''')

test("factorial", """int factorial(int n){
    if(n <= 1){ return 1; }
    return n * factorial(n - 1);
}
int main(){
    int r = factorial(5);
    printf("Result: %d\\n", r);
    return 0;
}""")

test("while loop", r'''
int main(){
    int i = 1;
    while(i <= 5){
        printf("%d ", i);
        i = i + 1;
    }
    printf("\n");
    return 0;
}
''')

test("multiple printf", r'''
int main(){
    printf("Hello, World!\n");
    int a = 10;
    int b = 20;
    printf("a=%d, b=%d, sum=%d\n", a, b, a + b);
    return 0;
}
''')
