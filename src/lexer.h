#ifndef LEXER_H
#define LEXER_H

#include <stdio.h>

#define MAX_TOKENS 1024

typedef struct Token {
    char type[20];
    char value[50];
    int line;
} Token;

extern Token tokens[MAX_TOKENS];
extern int token_count;

int is_keyword(const char *str);
int is_operator(const char *str);
int is_symbol(char c);
void add_token(const char *type, const char *value, int line);
void tokenize(const char *source);
void print_tokens();

#endif // LEXER_H
