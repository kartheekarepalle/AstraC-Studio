# Mini Programming Language Compiler - Design Document

## Overview
This compiler processes a simple programming language with assignment and arithmetic expressions, performing optimization and generating target code.

## Components
- **Lexer**: Tokenizes input source code.
- **Parser**: Builds an Abstract Syntax Tree (AST).
- **Semantic Analyzer**: Checks for semantic errors (e.g., undefined variables, type errors).
- **IR Generator**: Produces intermediate representation (IR) from AST.
- **Optimizer**: Performs optimizations (e.g., constant folding).
- **Code Generator**: Converts IR to target code (pseudo-assembly or three-address code).

## Example
Input:
```
x = 3 + 4 * 2;
```

Optimized IR:
```
('ASSIGN', '11', '_', 'x')
```

Target Code:
```
x = 11
```

## Extensibility
- Add more language features (control flow, functions, etc.)
- Implement more optimizations
- Target real assembly or bytecode
