import sys; sys.path.insert(0, 'api'); sys.path.insert(0, 'backend/app/services')
from compiler_pipeline import run_pipeline
from compile_run import TACInterpreter

def full_test(name, code):
    r = run_pipeline(code)
    tac = r.get('optimized_ir') or r.get('ir') or []
    errors = r.get('errors', [])
    if tac and not errors:
        interp = TACInterpreter(tac)
        runtime = interp.run()
    else:
        runtime = {
            'stdout': '',
            'stderr': '\n'.join(e.get('message', str(e)) for e in errors) or 'Compilation failed',
            'exit_code': 1,
            'execution_time_ms': None,
        }
    r['runtime'] = runtime
    print(f"--- {name} ---")
    print(f"  tokens: {len(r.get('tokens',[]))}")
    print(f"  syntax_tree: {'yes' if r.get('syntax_tree') else 'no'}")
    print(f"  semantic_tree: {'yes' if r.get('semantic_tree') else 'no'}")
    print(f"  ir: {len(r.get('ir',[]))} lines")
    print(f"  optimized_ir: {len(r.get('optimized_ir',[]))} lines")
    print(f"  assembly: {len(r.get('assembly',[]))} lines")
    print(f"  errors: {errors}")
    print(f"  phases: {len(r.get('phases',[]))}")
    print(f"  runtime.stdout: {repr(runtime['stdout'])}")
    print(f"  runtime.stderr: {repr(runtime.get('stderr',''))}")
    print(f"  runtime.exit_code: {runtime.get('exit_code')}")
    print()

full_test("hello world", r'''int main(){
    printf("Hello, World!\n");
    return 0;
}''')

full_test("arithmetic", r'''int main(){
    int x = 3 + 4;
    printf("%d\n", x);
    return 0;
}''')

full_test("loop sum", r'''int main(){
    int i;
    int sum = 0;
    for(i = 0; i < 5; i++){
        sum = sum + i;
    }
    printf("sum=%d\n", sum);
    return 0;
}''')

full_test("factorial", """int factorial(int n){
    if(n <= 1){ return 1; }
    return n * factorial(n - 1);
}
int main(){
    int r = factorial(5);
    printf("Result: %d\\n", r);
    return 0;
}""")

full_test("if/else", r'''int main(){
    int x = 10;
    if(x > 5){
        printf("big\n");
    } else {
        printf("small\n");
    }
    return 0;
}''')
