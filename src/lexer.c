// Tiny C Subset Compiler - Lexical Analyzer
// Implements: tokenize(const char *source)
// Prints tokens for debugging

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "lexer.h"
#include "output.h"



// Definitions in lexer.h, only define here:
Token tokens[MAX_TOKENS];
int token_count = 0;

static const char *keywords[] = {"int", "return", "if", "else", "while", NULL};
static const char *operators[] = {"+", "-", "*", "/", "=", "<", ">", "==", NULL};
static const char *symbols[] = {";", "{", "}", "(", ")", NULL};

int is_keyword(const char *str) {
    for (int i = 0; keywords[i]; i++) {
        if (strcmp(str, keywords[i]) == 0) return 1;
    }
    return 0;
}

int is_operator(const char *str) {
    for (int i = 0; operators[i]; i++) {
        if (strcmp(str, operators[i]) == 0) return 1;
    }
    return 0;
}

int is_symbol(char c) {
    for (int i = 0; symbols[i]; i++) {
        if (c == symbols[i][0]) return 1;
    }
    return 0;
}

void add_token(const char *type, const char *value, int line) {
    if (token_count >= MAX_TOKENS) return;
    strcpy(tokens[token_count].type, type);
    strcpy(tokens[token_count].value, value);
    tokens[token_count].line = line;
    token_count++;
}

void tokenize(const char *source) {
    int i = 0, line = 1;
    int len = strlen(source);
    while (i < len) {
        if (isspace(source[i])) {
            if (source[i] == '\n') line++;
            i++;
            continue;
        }
        // Skip comments (//... and /* ... */)
        if (source[i] == '/' && source[i+1] == '/') {
            while (i < len && source[i] != '\n') i++;
            continue;
        }
        if (source[i] == '/' && source[i+1] == '*') {
            i += 2;
            while (i < len && !(source[i] == '*' && source[i+1] == '/')) {
                if (source[i] == '\n') line++;
                i++;
            }
            i += 2;
            continue;
        }
        // Number
        if (isdigit(source[i])) {
            char num[50] = {0};
            int j = 0;
            while (i < len && isdigit(source[i])) {
                num[j++] = source[i++];
            }
            add_token("NUMBER", num, line);
            continue;
        }
        // Identifier or keyword
        if (isalpha(source[i]) || source[i] == '_') {
            char id[50] = {0};
            int j = 0;
            while (i < len && (isalnum(source[i]) || source[i] == '_')) {
                id[j++] = source[i++];
            }
            if (is_keyword(id))
                add_token("KEYWORD", id, line);
            else
                add_token("IDENTIFIER", id, line);
            continue;
        }
        // Operators (==, =, +, -, *, /, <, >)
        if (strchr("=+-*/<>", source[i])) {
            char op[3] = {0};
            op[0] = source[i];
            op[1] = 0;
            if ((source[i] == '=' || source[i] == '<' || source[i] == '>') && source[i+1] == '=') {
                op[1] = '=';
                op[2] = 0;
                i++;
            }
            add_token("OPERATOR", op, line);
            i++;
            continue;
        }
        // Symbols
        if (is_symbol(source[i])) {
            char sym[2] = {source[i], 0};
            add_token("SYMBOL", sym, line);
            i++;
            continue;
        }
        // Unknown character
        char unk[2] = {source[i], 0};
        printf("[Lexer Error] Unknown character '%c' at line %d\n", source[i], line);
        i++;
    }
}

void print_tokens() {
    if (json_mode) {
        output_tokens(tokens, token_count);
        return;
    }
    printf("--- TOKENS ---\n");
    for (int i = 0; i < token_count; i++) {
        printf("[%d] %s : %s\n", tokens[i].line, tokens[i].type, tokens[i].value);
    }
}
