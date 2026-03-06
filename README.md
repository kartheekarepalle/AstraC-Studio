<p align="center">
  <img src="https://img.shields.io/badge/AstraC-Studio-6366F1?style=for-the-badge&labelColor=0B0D14" alt="AstraC Studio" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=white&labelColor=0B0D14" alt="React 18" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white&labelColor=0B0D14" alt="FastAPI" />
  <img src="https://img.shields.io/badge/GCC-15.2-A42E2B?style=for-the-badge&logo=gnu&logoColor=white&labelColor=0B0D14" alt="GCC 15.2" />
  <img src="https://img.shields.io/badge/Tailwind-4-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white&labelColor=0B0D14" alt="Tailwind 4" />
</p>

<h1 align="center">AstraC Studio</h1>
<p align="center">
  <strong>A full-stack C compiler IDE with real-time analysis, interactive AST visualization, and program execution.</strong>
</p>
<p align="center">
  Built as a major project — Mini Programming Language Compiler with Optimization.
</p>

---

## Overview

AstraC Studio is a browser-based IDE that compiles, analyzes, and executes C programs. It combines a **Python-powered compiler front-end** (lexer, parser, semantic analysis, IR generation) with **GCC** for real compilation and execution — all presented through a premium, modern UI.

**Write C code → See tokens, AST, symbols, IR, assembly, and output — all in one screen.**

---

## Features

### Compiler Pipeline (6 Phases)

| Phase | Description |
|-------|-------------|
| **Lexical Analysis** | Regex-based C99 tokenizer — keywords, identifiers, numbers, operators, strings, chars, preprocessor directives, comments |
| **Syntax Tree (AST)** | Recursive-descent parser builds a JSON-serializable abstract syntax tree |
| **Semantic Analysis** | Symbol table extraction with variable names and types |
| **IR Generation** | Three-address-code intermediate representation |
| **Optimization** | Optimization pass framework (constant folding, extensible) |
| **Code Generation** | Real x86-64 assembly via `gcc -S`, plus full compilation and execution |

### IDE Features

- **Monaco Editor** — VS Code's editor with syntax highlighting, line numbers, and IntelliSense-style editing
- **8 Output Tabs** — Tokens, Syntax Tree, Symbols, IR, Optimized IR, Assembly, Output, Errors
- **Interactive AST Viewer** — Collapsible tree visualization with color-coded node types
- **Program Execution** — Compile and run with stdout/stderr capture, exit codes, and execution timing
- **Stdin Support** — Provide input for programs that use `scanf`/`gets`
- **Dark / Light Theme** — Premium SaaS aesthetic with glassmorphism, gradients, and Framer Motion animations
- **Keyboard Shortcuts** — `Ctrl + Enter` to compile and run
- **Health Monitoring** — Real-time backend status indicator

### Supported C Language Features

- Functions (definitions, declarations, parameters, pointers, arrays)
- Variables (declarations, initializers, pointer types, array types)
- Control flow (`if`/`else`, `while`, `for`, `do`/`while`, `switch`/`case`)
- Expressions (arithmetic, assignments, function calls, nested expressions)
- Structs, arrays, initializer lists
- Preprocessor directives (`#include`, `#define`, etc.)
- Comments (line `//` and block `/* */`)
- Strings and character literals with escape sequences
- Full C99/C11 support through GCC backend

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, Vite 5, Tailwind CSS 4, Framer Motion, Lucide React, Monaco Editor |
| **Backend** | Python, FastAPI, Uvicorn |
| **Compiler** | Custom lexer + parser + semantic analyzer + IR generator (Python), GCC 15.2 (MinGW-w64) |
| **Optional** | Docker (sandboxed TinyC analysis) |

---

## Project Structure

```
AstraC Studio/
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── App.jsx             # Main application shell
│   │   ├── styles.css          # Theme system (dark/light, glassmorphism)
│   │   ├── components/
│   │   │   ├── Editor.jsx      # Monaco code editor
│   │   │   ├── OutputTabs.jsx  # 8-tab output panel with animations
│   │   │   ├── SyntaxTree.jsx  # Interactive AST tree viewer
│   │   │   ├── Spinner.jsx     # Loading overlay
│   │   │   └── HealthBanner.jsx# Backend status banner
│   │   └── services/
│   │       └── api.js          # API client
│   ├── package.json
│   └── vite.config.js
│
├── backend/                    # FastAPI server
│   ├── app/
│   │   ├── main.py             # API endpoints & health check
│   │   └── services/
│   │       ├── executor.py     # GCC compilation & execution
│   │       └── tinyc_adapter.py# TinyC binary adapter
│   └── requirements.txt
│
├── src/
│   ├── c_compiler/             # Full C compiler front-end
│   │   ├── lexer.py            # C99 tokenizer (CLexer)
│   │   ├── parser.py           # Recursive-descent parser
│   │   ├── ast_builder.py      # AST construction (~380 lines)
│   │   ├── semantic.py         # Semantic analysis & symbol table
│   │   ├── ir.py               # Three-address-code IR generator
│   │   ├── optimizer.py        # IR optimization pass
│   │   ├── codegen.py          # Target code generation
│   │   └── main.py             # Pipeline orchestrator
│   ├── *.c / *.h               # C reference implementations
│   └── *.py                    # Simple expression compiler
│
├── mingw64/                    # Bundled GCC toolchain
├── docker/                     # Docker config for TinyC
├── tests/                      # Test suites
├── tools/                      # E2E compile-and-run scripts
├── scripts/                    # Backend launch scripts
└── docs/                       # Design documentation
```

---

## Quickstart

### Prerequisites

- **Python 3.10+** with `pip`
- **Node.js 18+** with `npm`
- **GCC** — bundled MinGW-w64 in `mingw64/`, or install your own

### 1. Clone & Install

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies
cd ../frontend
npm install
```

### 2. Start the Backend

```bash
cd backend
py -3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

The backend auto-discovers GCC from the bundled `mingw64/` directory or your system PATH.

### 3. Start the Frontend

```bash
cd frontend
npm run dev
```

### 4. Open in Browser

Navigate to **http://127.0.0.1:5173** — write C code and hit **Run Code** (or `Ctrl + Enter`).

---

## API Reference

### `GET /api/health`

Returns backend status and GCC availability.

```json
{
  "ok": true,
  "gcc_path": "C:\\...\\gcc.EXE",
  "gcc_found": true,
  "pipeline": "local",
  "hint": null
}
```

### `POST /api/compile-run`

Compiles and executes C source code. Returns all compiler phases and runtime output.

**Request:**
```json
{
  "source": "#include <stdio.h>\nint main() { printf(\"Hello\"); return 0; }",
  "stdin": "",
  "timeout": 10,
  "mode": "local"
}
```

**Response:**
```json
{
  "tokens": [{"type": "KEYWORD", "value": "int"}, ...],
  "ast": {"type": "Program", "children": [...]},
  "symbol_table": [{"name": "main", "type": "int", "scope": "global"}],
  "intermediate_code": ["t0 = call printf, \"Hello\"", ...],
  "optimized_code": ["t0 = call printf, \"Hello\"", ...],
  "assembly": ".file \"source.c\"\n.text\n...",
  "stdout": "Hello",
  "stderr": "",
  "exit_code": 0,
  "exec_time_ms": 42,
  "errors": []
}
```

---

## Output Tabs

| Tab | Icon | Description |
|-----|------|-------------|
| **Tokens** | `List` | Full token stream with type and value columns |
| **Syntax Tree** | `GitBranch` | Interactive collapsible AST with color-coded node types |
| **Symbols** | `Database` | Symbol table — variable names, types, and scopes |
| **IR** | `FileCode` | Three-address-code intermediate representation |
| **Optimized** | `Sparkles` | Optimized intermediate code |
| **Assembly** | `Cpu` | Real x86-64 assembly output from `gcc -S` |
| **Output** | `Play` | Program stdout, stderr, exit code, and execution time |
| **Errors** | `AlertTriangle` | Compilation and analysis errors with line numbers |

---

## Configuration

### GCC Path

The backend searches for GCC in this order:

1. Bundled `mingw64/bin/gcc.EXE` (relative to project root)
2. Known WinLibs installation paths
3. System `PATH`

To override, set the `GCC_PATH` environment variable.

### TinyC Binary (Optional)

For additional analysis via the TinyC helper binary:

```bash
# Environment variable
set TINYC_PATH=C:\path\to\tinyc.exe

# Or in .env file at project root
TINYC_PATH=C:\path\to\tinyc.exe
```

### Docker Sandbox (Optional)

Run TinyC analysis in a sandboxed container:

```bash
cd docker/tinyc
docker build -t mini-compiler-tinyc:local .
```

Set `TINYC_DOCKER_IMAGE=mini-compiler-tinyc:local` in your environment or `.env` file.

---

## UI Themes

AstraC Studio ships with two carefully crafted themes:

| | Dark Mode | Light Mode |
|---|-----------|------------|
| **Background** | `#0B0D14` | `#F3F5F9` |
| **Cards** | `rgba(22,25,38,0.65)` | `rgba(255,255,255,0.92)` |
| **Accent** | `#6366F1` | `#6366F1` |
| **Borders** | `rgba(255,255,255,0.06)` | `#E2E6EF` |

Both themes feature glassmorphism effects, layered gradient backgrounds, elevated shadows, and smooth Framer Motion transitions.

---

## Development

```bash
# Run backend with auto-reload
cd backend && py -3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

# Run frontend with HMR
cd frontend && npm run dev

# Run tests
cd tests && py -3 -m pytest

# Build for production
cd frontend && npm run build
```

---

## License

This project was built as a major academic project — Mini Programming Language Compiler with Optimization.

---

<p align="center">
  <strong>AstraC Studio</strong> — Write. Compile. Visualize. Execute.<br/>
  <sub>Built with React, FastAPI, and GCC</sub>
</p>
```