# C-Minus Compiler

A one-pass compiler implementation for the C-Minus programming language, developed as a Compiler Design course project at Sharif University of Technology.

The compiler translates C-Minus source programs through the main compilation stages:
- Lexical Analysis
- Syntax Analysis
- Semantic Analysis
- Intermediate Code Generation

The implementation is developed in Python.

---

## Overview

This project implements a simplified compiler pipeline for the C-Minus language. 
The compiler processes an input program in a single pass and generates intermediate three-address code as the final output.

The compiler modules are integrated as a pipeline where each phase provides the required information for subsequent stages.

---

# Compiler Phases

## 1. Lexical Analyzer (Scanner)

The scanner reads the input source code character by character and converts it into a sequence of tokens.

Implemented features:

- Recognition of:
  - keywords
  - identifiers
  - numbers
  - symbols
  - comments

- Symbol table construction
- Line number tracking
- Lexical error detection and recovery

Generated outputs:
