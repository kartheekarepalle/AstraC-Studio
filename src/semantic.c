// Tiny C Subset Compiler - Semantic Analyzer
// Implements: symbol table, variable checks
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "lexer.h"
#include "semantic.h"
#include "output.h"

#define MAX_SYMBOLS 256

typedef struct {
    char name[50];
} Symbol;

Symbol symbol_table[MAX_SYMBOLS];
int symbol_count = 0;

int lookupSymbol(const char *name) {
    for (int i = 0; i < symbol_count; i++) {
        if (strcmp(symbol_table[i].name, name) == 0) return 1;
    }
    return 0;
}

void insertSymbol(const char *name) {
    if (lookupSymbol(name)) {
        printf("[Semantic Error] Duplicate declaration of '%s'\n", name);
        exit(1);
    }
    if (symbol_count >= MAX_SYMBOLS) {
        printf("[Semantic Error] Symbol table overflow\n");
        exit(1);
    }
    strcpy(symbol_table[symbol_count++].name, name);
}

void semantic_check() {
    symbol_count = 0;
    for (int i = 0; i < token_count; i++) {
        if (strcmp(tokens[i].type, "KEYWORD") == 0 && strcmp(tokens[i].value, "int") == 0) {
            if (i+1 < token_count && strcmp(tokens[i+1].type, "IDENTIFIER") == 0) {
                insertSymbol(tokens[i+1].value);
            }
        }
        if (strcmp(tokens[i].type, "IDENTIFIER") == 0) {
            // Check if used in assignment or expression (not declaration)
            int is_decl = (i > 0 && strcmp(tokens[i-1].type, "KEYWORD") == 0 && strcmp(tokens[i-1].value, "int") == 0);
            if (!is_decl && !lookupSymbol(tokens[i].value)) {
                printf("[Semantic Error] Undeclared variable '%s' at line %d\n", tokens[i].value, tokens[i].line);
                exit(1);
            }
        }
    }
    if (json_mode) {
        const char *names[MAX_SYMBOLS];
        for (int i = 0; i < symbol_count; ++i) names[i] = symbol_table[i].name;
        output_string_array("symbol_table", names, symbol_count);
        return;
    }
    printf("--- SYMBOL TABLE ---\n");
    for (int i = 0; i < symbol_count; i++) {
        printf("%s\n", symbol_table[i].name);
    }
}
