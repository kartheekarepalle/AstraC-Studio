// Tiny C Subset Compiler - Code Generator (Pseudo Assembly)
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "intermediate.h"
#include "codegen.h"
#include "output.h"

void generateAssembly() {
    if (!json_mode) printf("--- ASSEMBLY ---\n");

    /* Collect assembly lines and either print them or emit JSON */
    int idx = 0;
    int max_lines = tac_count * 4 + 8;
    if (max_lines < 8) max_lines = 8;
    char (*lines)[100] = malloc(max_lines * sizeof *lines);
    if (!lines) {
        /* fallback to printing directly */
        for (int i = 0; i < tac_count; i++) {
            printf("; %s\n", tac[i]);
        }
        return;
    }

    for (int i = 0; i < tac_count; i++) {
        char lhs[20], op1[20], op[5], op2[20];
        if (sscanf(tac[i], "%s = %s %s %s", lhs, op1, op, op2) == 4) {
            if (idx + 4 >= max_lines) break;
            snprintf(lines[idx++], 100, "MOV R1, %s", op1);
            if (strcmp(op, "+") == 0) snprintf(lines[idx++], 100, "ADD R1, %s", op2);
            else if (strcmp(op, "-") == 0) snprintf(lines[idx++], 100, "SUB R1, %s", op2);
            else if (strcmp(op, "*") == 0) snprintf(lines[idx++], 100, "MUL R1, %s", op2);
            else if (strcmp(op, "/") == 0) snprintf(lines[idx++], 100, "DIV R1, %s", op2);
            snprintf(lines[idx++], 100, "MOV %s, R1", lhs);
        } else if (sscanf(tac[i], "%s = %s", lhs, op1) == 2) {
            if (idx + 1 >= max_lines) break;
            snprintf(lines[idx++], 100, "MOV %s, %s", lhs, op1);
        } else if (strstr(tac[i], "return") != NULL) {
            char ret[20];
            sscanf(tac[i], "return %s", ret);
            if (idx + 1 >= max_lines) break;
            snprintf(lines[idx++], 100, "RET %s", ret);
        } else {
            if (idx + 1 >= max_lines) break;
            snprintf(lines[idx++], 100, "; %s", tac[i]);
        }
    }

    if (json_mode) {
        output_lines_2d("assembly", lines, idx);
    } else {
        for (int j = 0; j < idx; ++j) printf("%s\n", lines[j]);
    }

    free(lines);
}
