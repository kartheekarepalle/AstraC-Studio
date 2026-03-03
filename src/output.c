#include "output.h"
#include <string.h>

int json_mode = 0;
static int first_field = 1;

static void print_comma_if_needed() {
    if (!first_field) printf(",\n");
    else { first_field = 0; printf("\n"); }
}

static void escape_and_print(const char *s) {
    putchar('"');
    for (const unsigned char *p = (const unsigned char*)s; *p; ++p) {
        unsigned char c = *p;
        switch (c) {
            case '"': printf("\\\""); break;
            case '\\': printf("\\\\"); break;
            case '\b': printf("\\b"); break;
            case '\f': printf("\\f"); break;
            case '\n': printf("\\n"); break;
            case '\r': printf("\\r"); break;
            case '\t': printf("\\t"); break;
            default:
                if (c < 32) printf("\\u%04x", c);
                else putchar(c);
        }
    }
    putchar('"');
}

void output_init() {
    if (!json_mode) return;
    printf("{");
    first_field = 1;
}

void output_finalize() {
    if (!json_mode) return;
    printf("\n}\n");
}

void output_tokens(Token *tokens, int token_count) {
    if (!json_mode) return;
    print_comma_if_needed();
    printf("  \"tokens\": [\n");
    for (int i = 0; i < token_count; ++i) {
        printf("    {");
        printf("\"line\": %d, ", tokens[i].line);
        printf("\"type\": "); escape_and_print(tokens[i].type); printf(", ");
        printf("\"value\": "); escape_and_print(tokens[i].value);
        printf("}");
        if (i + 1 < token_count) printf(",\n"); else printf("\n");
    }
    printf("  ]");
}

void output_string_array(const char *field_name, const char **items, int count) {
    if (!json_mode) return;
    print_comma_if_needed();
    printf("  \"");
    printf("%s", field_name);
    printf("\": [\n");
    for (int i = 0; i < count; ++i) {
        printf("    "); escape_and_print(items[i]);
        if (i + 1 < count) printf(",\n"); else printf("\n");
    }
    printf("  ]");
}

void output_lines_2d(const char *field_name, char arr[][100], int count) {
    if (!json_mode) return;
    print_comma_if_needed();
    printf("  \""); printf("%s", field_name); printf("\": [\n");
    for (int i = 0; i < count; ++i) {
        printf("    "); escape_and_print(arr[i]);
        if (i + 1 < count) printf(",\n"); else printf("\n");
    }
    printf("  ]");
}

void output_lines(const char *field_name, const char **lines, int count) {
    if (!json_mode) return;
    print_comma_if_needed();
    printf("  \""); printf("%s", field_name); printf("\": [\n");
    for (int i = 0; i < count; ++i) {
        printf("    "); escape_and_print(lines[i]);
        if (i + 1 < count) printf(",\n"); else printf("\n");
    }
    printf("  ]");
}

void output_error(const char *stage, const char *msg, int line) {
    if (!json_mode) return;
    print_comma_if_needed();
    printf("  \"errors\": [\n");
    printf("    {\"stage\": "); escape_and_print(stage); printf(", \"msg\": "); escape_and_print(msg);
    if (line >= 0) printf(", \"line\": %d", line);
    printf("}];");
}
