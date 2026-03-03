// Tiny C Subset Compiler - Main Driver
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "lexer.h"
#include "parser.h"
#include "semantic.h"
#include "intermediate.h"
#include "optimizer.h"
#include "codegen.h"
#include "output.h"

// control JSON output mode from CLI (defined in output.c)

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <sourcefile.c> [--json]\n", argv[0]);
        return 1;
    }

    const char *input_path = NULL;
    for (int i = 1; i < argc; ++i) {
        const char *a = argv[i];
        if (a[0] == '-') {
            if (strcmp(a, "--json") == 0 || strcmp(a, "-j") == 0) {
                json_mode = 1;
                continue;
            }
            // unknown flag: ignore or could report
            continue;
        }
        if (!input_path) input_path = a;
    }
    if (!input_path) {
        printf("Usage: %s <sourcefile.c> [--json]\n", argv[0]);
        return 1;
    }

    /* debug: removed extra prints to keep JSON output clean */

    FILE *f = fopen(input_path, "r");
    if (!f) {
        printf("Could not open file %s\n", input_path);
        return 1;
    }
    char *source = malloc(10000);
    size_t n = fread(source, 1, 9999, f);
    source[n] = '\0';
    fclose(f);

    // initialize JSON output if requested
    output_init();

    tokenize(source);
    print_tokens();
    parse();
    semantic_check();
    generateIR();
    optimizeIR();
    generateAssembly();

    output_finalize();
    free(source);
    return 0;
}
