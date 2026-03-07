import sys, json
sys.path.insert(0, 'backend/app/services')
from compiler_pipeline import phase_lexical, phase_syntax, render_ascii_tree, phase_semantic, phase_intermediate, phase_optimization, phase_codegen

code = r"""int main() {
    int N, i, sum;
    int base = 10;
    int multiplier = 4;
    int offset = base * multiplier;
    N = 5;
    sum = 0;
    for(i = 0; i < N; i++) {
        sum = sum + i;
    }
    int result = sum + offset;
    printf("Result = %d\n", result);
    return 0;
}"""

with open('test_tree_output.txt', 'w') as f:
    # Phase 1
    r1 = phase_lexical(code)
    f.write("=== Phase 1: Lexical ===\n")
    f.write(f"Tokens: {len(r1['tokens'])}, Errors: {r1['errors']}\n\n")

    # Phase 2
    r2 = phase_syntax(r1['tokens'])
    f.write("=== Phase 2: Syntax Tree ===\n")
    f.write(render_ascii_tree(r2['syntax_tree']))
    f.write(f"\nErrors: {r2['errors']}\n\n")

    # Phase 3
    r3 = phase_semantic(r1['tokens'], r2['syntax_tree'])
    f.write("=== Phase 3: Semantic ===\n")
    f.write(f"Symbol Table: {json.dumps(r3['symbol_table'], indent=2)}\n")
    f.write(f"Errors: {r3['errors']}\n\n")

    # Phase 4
    r4 = phase_intermediate(r1['tokens'])
    tac_lines = r4.get('ir', [])
    f.write("=== Phase 4: IR (TAC) ===\n")
    for line in tac_lines:
        f.write(line + '\n')
    f.write(f"Errors: {r4['errors']}\n\n")

    # Phase 5
    r5 = phase_optimization(tac_lines)
    opt_lines = r5.get('optimized_ir', [])
    opt_changes = r5.get('changes', [])
    f.write("=== Phase 5: Optimized IR ===\n")
    for line in opt_lines:
        f.write(line + '\n')
    f.write(f"\nOptimizations Applied ({len(opt_changes)}):\n")
    for ch in opt_changes:
        f.write(f"  [{ch['rule']}] {ch['original']} -> {ch['optimized']}\n")
    f.write(f"Errors: {r5['errors']}\n\n")

    # Phase 6
    r6 = phase_codegen(opt_lines if opt_lines else tac_lines)
    f.write("=== Phase 6: Code Generation ===\n")
    if isinstance(r6.get('assembly'), list):
        for line in r6['assembly']:
            f.write(line + '\n')
    f.write(f"Errors: {r6['errors']}\n")

print("Done - wrote test_tree_output.txt")
