// Tiny C Subset Compiler - Syntax Analyzer (Recursive Descent)
// Implements: parse() using tokens from lexer.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "lexer.h"
#include "parser.h"
#include "output.h"

int current = 0;

Token *get_token() {
    if (current < token_count)
        return &tokens[current];
    return NULL;
}

void advance() {
    if (current < token_count)
        current++;
}

int match(const char *type, const char *value) {
    Token *tok = get_token();
    if (!tok) return 0;
    if (strcmp(tok->type, type) == 0 && (!value || strcmp(tok->value, value) == 0)) {
        advance();
        return 1;
    }
    return 0;
}

void syntax_error(const char *msg) {
    Token *tok = get_token();
    int line = tok ? tok->line : -1;
    printf("[Syntax Error] %s at line %d\n", msg, line);
    exit(1);
}

// Forward declarations
void program();
void function();
void stmt_list();
void stmt();
void declaration();
void assignment();
void if_stmt();
void while_stmt();
void return_stmt();
void expr();
void term();
void factor();
void condition();

void expect(const char *type, const char *value) {
    if (!match(type, value)) {
        char msg[100];
        sprintf(msg, "Expected %s '%s'", type, value ? value : "");
        syntax_error(msg);
    }
}

void program() {
    function();
    if (current < token_count) syntax_error("Extra tokens after program end");
}

void function() {
    expect("KEYWORD", "int");
    expect("IDENTIFIER", "main");
    expect("SYMBOL", "(");
    expect("SYMBOL", ")");
    expect("SYMBOL", "{");
    stmt_list();
    expect("SYMBOL", "}");
}

void stmt_list() {
    while (1) {
        Token *tok = get_token();
        if (!tok || (strcmp(tok->type, "SYMBOL") == 0 && strcmp(tok->value, "}") == 0))
            break;
        stmt();
    }
}

void stmt() {
    Token *tok = get_token();
    if (!tok) return;
    if (strcmp(tok->type, "KEYWORD") == 0 && strcmp(tok->value, "int") == 0) {
        declaration();
    } else if (strcmp(tok->type, "IDENTIFIER") == 0) {
        assignment();
    } else if (strcmp(tok->type, "KEYWORD") == 0 && strcmp(tok->value, "if") == 0) {
        if_stmt();
    } else if (strcmp(tok->type, "KEYWORD") == 0 && strcmp(tok->value, "while") == 0) {
        while_stmt();
    } else if (strcmp(tok->type, "KEYWORD") == 0 && strcmp(tok->value, "return") == 0) {
        return_stmt();
    } else {
        syntax_error("Invalid statement");
    }
}

void declaration() {
    expect("KEYWORD", "int");
    expect("IDENTIFIER", NULL);
    expect("SYMBOL", ";");
}

void assignment() {
    expect("IDENTIFIER", NULL);
    expect("OPERATOR", "=");
    expr();
    expect("SYMBOL", ";");
}

void if_stmt() {
    expect("KEYWORD", "if");
    expect("SYMBOL", "(");
    condition();
    expect("SYMBOL", ")");
    expect("SYMBOL", "{");
    stmt_list();
    expect("SYMBOL", "}");
    Token *tok = get_token();
    if (tok && strcmp(tok->type, "KEYWORD") == 0 && strcmp(tok->value, "else") == 0) {
        advance();
        expect("SYMBOL", "{");
        stmt_list();
        expect("SYMBOL", "}");
    }
}

void while_stmt() {
    expect("KEYWORD", "while");
    expect("SYMBOL", "(");
    condition();
    expect("SYMBOL", ")");
    expect("SYMBOL", "{");
    stmt_list();
    expect("SYMBOL", "}");
}

void return_stmt() {
    expect("KEYWORD", "return");
    expr();
    expect("SYMBOL", ";");
}

void condition() {
    expr();
    Token *tok = get_token();
    if (tok && strcmp(tok->type, "OPERATOR") == 0 && 
        (strcmp(tok->value, "<") == 0 || strcmp(tok->value, ">") == 0 || strcmp(tok->value, "==") == 0)) {
        advance();
        expr();
    } else {
        syntax_error("Expected relational operator in condition");
    }
}

void expr() {
    term();
    Token *tok = get_token();
    while (tok && strcmp(tok->type, "OPERATOR") == 0 && (strcmp(tok->value, "+") == 0 || strcmp(tok->value, "-") == 0)) {
        advance();
        term();
        tok = get_token();
    }
}

void term() {
    factor();
    Token *tok = get_token();
    while (tok && strcmp(tok->type, "OPERATOR") == 0 && (strcmp(tok->value, "*") == 0 || strcmp(tok->value, "/") == 0)) {
        advance();
        factor();
        tok = get_token();
    }
}

void factor() {
    Token *tok = get_token();
    if (!tok) syntax_error("Unexpected end of input in factor");
    if (strcmp(tok->type, "IDENTIFIER") == 0 || strcmp(tok->type, "NUMBER") == 0) {
        advance();
    } else {
        syntax_error("Expected identifier or number in expression");
    }
}

void parse() {
    current = 0;
    program();
    if (!json_mode) printf("--- PARSE SUCCESS ---\n");
}
