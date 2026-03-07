import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from compiler_pipeline import run_pipeline

source = r'''
#include <stdio.h>
int main() {
    int x = 2;
    switch (x) {
    case 1:
        printf("one\n");
        break;
    case 2:
        printf("two\n");
        break;
    default:
        printf("other\n");
    }
    return 0;
}
'''

print("Running pipeline...")
result = run_pipeline(source)
if result.get('errors'):
    print('ERRORS:', result['errors'])
else:
    tac = result.get('optimized_ir') or result.get('ir') or []
    print('TAC:')
    for l in tac:
        print(f'  {l}')
print("Done")
