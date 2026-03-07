import sys; sys.path.insert(0, 'backend/app/services')
from compiler_pipeline import run_pipeline

code = r'''int main(){
    int a, b;
    printf("Enter two integers: ");
    scanf("%d %d", &a, &b);
    printf("Sum: %d\n", a + b);
    return 0;
}'''
r = run_pipeline(code)
print("IR:")
for line in r['ir']: print(' ', repr(line))
print("\nOptimized IR:")
for line in r['optimized_ir']: print(' ', repr(line))
