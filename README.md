# C-Minus Compiler

An educational compiler implementation for the C-Minus programming language, developed as a Compiler Design course project.

The project implements the front-end phases of a compiler, including lexical analysis, LL(1) syntax parsing, parse tree generation, and syntax error detection.

## Features

### Lexical Analyzer (Scanner)

- Tokenizes source code into:
  - keywords
  - identifiers
  - numbers
  - symbols
- Supports whitespace handling and comment processing.

### LL(1) Parser

- Implements predictive parsing using:
  - context-free grammar rules
  - FIRST and FOLLOW sets
  - LL(1) parse table construction
- Generates a parse tree representation of the input program.

### Error Detection and Recovery

- Detects syntax errors during parsing.
- Implements panic-mode error recovery to continue parsing after invalid input.

## Project Structure
