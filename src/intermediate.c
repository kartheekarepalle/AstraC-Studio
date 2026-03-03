// Tiny C Subset Compiler - Intermediate Representation (Three Address Code)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "lexer.h"
#include "intermediate.h"
#include "output.h"


char tac[MAX_TAC][100];
int tac_count = 0;
int temp_counter = 1;
int label_counter = 1;

char* new_temp() {
    static char t[10];
    sprintf(t, "t%d", temp_counter++);
    return t;
}

char* new_label() {
    static char l[10];
    sprintf(l, "L%d", label_counter++);
    return l;
}

void add_tac(const char *code) {
    if (tac_count < MAX_TAC) {
        strcpy(tac[tac_count++], code);
    }
}

// For demo: generate TAC for assignments only (expand for full subset as needed)
void generateIR() {
    tac_count = 0;
    for (int i = 0; i < token_count; i++) {
        if (strcmp(tokens[i].type, "IDENTIFIER") == 0 && i+2 < token_count && strcmp(tokens[i+1].type, "OPERATOR") == 0 && strcmp(tokens[i+1].value, "=") == 0) {
            // assignment: a = b + c ;
            char code[100];
            if (strcmp(tokens[i+3].type, "OPERATOR") == 0 && (strcmp(tokens[i+3].value, "+") == 0 || strcmp(tokens[i+3].value, "-") == 0 || strcmp(tokens[i+3].value, "*") == 0 || strcmp(tokens[i+3].value, "/") == 0)) {
                // a = b + c
                char temp[10];
                strcpy(temp, new_temp());
                sprintf(code, "%s = %s %s %s", temp, tokens[i+2].value, tokens[i+3].value, tokens[i+4].value);
                add_tac(code);
                sprintf(code, "%s = %s", tokens[i].value, temp);
                add_tac(code);
            } else {
                // a = b
                sprintf(code, "%s = %s", tokens[i].value, tokens[i+2].value);
                add_tac(code);
            }
        }
    }
    if (json_mode) {
        output_lines_2d("intermediate_code", tac, tac_count);
        return;
    }
    printf("--- INTERMEDIATE CODE ---\n");
    for (int i = 0; i < tac_count; i++) {
        printf("%s\n", tac[i]);
    }
}
