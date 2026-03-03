// Tiny C Subset Compiler - Optimizer (Constant Folding, Algebraic Simplification)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "intermediate.h"
#include "optimizer.h"
#include "output.h"

void optimizeIR() {
    if (json_mode) {
        // Build a temporary array of optimized lines and output as JSON
        char out_lines[MAX_TAC][100];
        int out_count = 0;
        for (int i = 0; i < tac_count; i++) {
            char *line = tac[i];
            char lhs[20], op1[20], op[5], op2[20];
            int optimized = 0;
            if (sscanf(line, "%s = %s %s %s", lhs, op1, op, op2) == 4) {
                if (isdigit(op1[0]) && isdigit(op2[0])) {
                    int n1 = atoi(op1), n2 = atoi(op2), res = 0;
                    if (strcmp(op, "+") == 0) res = n1 + n2;
                    else if (strcmp(op, "-") == 0) res = n1 - n2;
                    else if (strcmp(op, "*") == 0) res = n1 * n2;
                    else if (strcmp(op, "/") == 0 && n2 != 0) res = n1 / n2;
                    snprintf(out_lines[out_count++], 100, "%s = %d", lhs, res);
                    optimized = 1;
                }
                if (!optimized) {
                    if ((strcmp(op, "*") == 0 && strcmp(op2, "1") == 0) || (strcmp(op, "*") == 0 && strcmp(op1, "1") == 0)) {
                        snprintf(out_lines[out_count++], 100, "%s = %s", lhs, strcmp(op1, "1") == 0 ? op2 : op1);
                        optimized = 1;
                    } else if ((strcmp(op, "+") == 0 && strcmp(op2, "0") == 0) || (strcmp(op, "+") == 0 && strcmp(op1, "0") == 0)) {
                        snprintf(out_lines[out_count++], 100, "%s = %s", lhs, strcmp(op1, "0") == 0 ? op2 : op1);
                        optimized = 1;
                    } else if ((strcmp(op, "*") == 0 && (strcmp(op1, "0") == 0 || strcmp(op2, "0") == 0))) {
                        snprintf(out_lines[out_count++], 100, "%s = 0", lhs);
                        optimized = 1;
                    }
                }
            }
            if (!optimized) {
                snprintf(out_lines[out_count++], 100, "%s", line);
            }
        }
        output_lines_2d("optimized_code", out_lines, out_count);
        return;
    }
    printf("--- OPTIMIZED CODE ---\n");
    for (int i = 0; i < tac_count; i++) {
        char *line = tac[i];
        char lhs[20], op1[20], op[5], op2[20];
        // Try to match tX = N op N
        if (sscanf(line, "%s = %s %s %s", lhs, op1, op, op2) == 4) {
            if (isdigit(op1[0]) && isdigit(op2[0])) {
                int n1 = atoi(op1), n2 = atoi(op2), res = 0;
                if (strcmp(op, "+") == 0) res = n1 + n2;
                else if (strcmp(op, "-") == 0) res = n1 - n2;
                else if (strcmp(op, "*") == 0) res = n1 * n2;
                else if (strcmp(op, "/") == 0 && n2 != 0) res = n1 / n2;
                printf("%s = %d\n", lhs, res);
                continue;
            }
            // Algebraic simplification
            if ((strcmp(op, "*") == 0 && strcmp(op2, "1") == 0) || (strcmp(op, "*") == 0 && strcmp(op1, "1") == 0)) {
                printf("%s = %s\n", lhs, strcmp(op1, "1") == 0 ? op2 : op1);
                continue;
            }
            if ((strcmp(op, "+") == 0 && strcmp(op2, "0") == 0) || (strcmp(op, "+") == 0 && strcmp(op1, "0") == 0)) {
                printf("%s = %s\n", lhs, strcmp(op1, "0") == 0 ? op2 : op1);
                continue;
            }
            if ((strcmp(op, "*") == 0 && (strcmp(op1, "0") == 0 || strcmp(op2, "0") == 0))) {
                printf("%s = 0\n", lhs);
                continue;
            }
        }
        // Default: print as is
        printf("%s\n", line);
    }
}
