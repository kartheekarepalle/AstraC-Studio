# C Compiler Project - Design Document

## Overview
This project scaffolds a full C99/C11 compiler, with modular components for each compilation stage. The initial implementation is a stub pipeline, ready for incremental extension to full C support.

## Structure
- `lexer.py`: Tokenizes C source code, recognizes C99 keywords and symbols.
- `parser.py`: Parses tokens into an AST, stubbed for function definitions.
- `semantic.py`: Semantic analysis, symbol table, type checks (stub).
- `ir.py`: Intermediate representation generation (stub).
- `optimizer.py`: IR optimization (stub).
- `codegen.py`: Target code generation (stub).
- `main.py`: Pipeline driver.

## Extending to Full C
- Expand parser to support all C99 grammar rules (declarations, expressions, control flow, etc.)
- Implement full semantic analysis (types, scopes, function signatures)
- Add IR for all C constructs
- Implement optimizations and real code generation (assembly, LLVM IR, etc.)

## Testing
- Place C test programs in `tests/c_compiler/`
- Add unit and integration tests for each stage

## Note
Building a full C compiler is a long-term, multi-person project. This scaffold enables professional, incremental development.