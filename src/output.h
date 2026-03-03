#ifndef OUTPUT_H
#define OUTPUT_H

#include <stdio.h>
#include "lexer.h"

extern int json_mode;

void output_init();
void output_finalize();
void output_tokens(Token *tokens, int token_count);
void output_string_array(const char *field_name, const char **items, int count);
void output_lines_2d(const char *field_name, char arr[][100], int count);
void output_lines(const char *field_name, const char **lines, int count);
void output_error(const char *stage, const char *msg, int line);

#endif // OUTPUT_H
