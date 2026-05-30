# Keyhan Masoudi 401106509
# Yousef Sadidi 401117509



KEYWORDS_LIST = [
    'break', 'else', 'for', 'if', 'int', 'return', 'void',
    'goto', 'switch', 'case', 'default', 'while'
]
KEYWORDS = set(KEYWORDS_LIST)
SINGLE_SYMBOLS = set(';:,[](){}+-*/=<')


class Scanner:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.lineno = 1
        self.tokens = {}
        self.errors = {}
        self.symbol_table = list(KEYWORDS_LIST)
        self._symbol_set = set(KEYWORDS_LIST)

    def _peek(self, offset=0):
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else None

    def _advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.lineno += 1
        return ch

    def _add_token(self, lineno, ttype, tval):
        self.tokens.setdefault(lineno, []).append((ttype, tval))

    def _add_error(self, lineno, string, message):
        self.errors.setdefault(lineno, []).append((string, message))

    def _add_symbol(self, lexeme):
        if lexeme not in self._symbol_set:
            self._symbol_set.add(lexeme)
            self.symbol_table.append(lexeme)

    def get_next_token(self):
        while self.pos < len(self.source):
            ch = self._peek()

            # --- WHITESPACE: skip, but track line changes ---
            if ch in {' ', '\n', '\r', '\t', '\v', '\f'}:
                self._advance()
                continue

            start_lineno = self.lineno

            # --- SINGLE-LINE COMMENT: // ---
            if ch == '/' and self._peek(1) == '/':
                self._advance()
                self._advance()
                while self.pos < len(self.source) and self._peek() != '\n':
                    self._advance()
                continue

            # --- MULTI-LINE COMMENT: /* ... */ ---
            if ch == '/' and self._peek(1) == '*':
                comment_start = self.pos
                self._advance()  # /
                self._advance()  # *

                closed = False
                while self.pos < len(self.source):
                    if self._peek() == '*' and self._peek(1) == '/':
                        self._advance()
                        self._advance()
                        closed = True
                        break
                    self._advance()

                if not closed:
                    # Unclosed comment consumes until EOF.
                    raw = self.source[comment_start: comment_start + 9]
                    display = raw + '...' if len(self.source) - comment_start > len(raw) else raw
                    self._add_error(start_lineno, display, 'Unclosed comment')
                continue

            # --- UNMATCHED COMMENT: */ outside a comment ---
            if ch == '*' and self._peek(1) == '/':
                self._advance()
                self._advance()
                self._add_error(start_lineno, '*/', 'Unmatched comment')
                continue

            # --- NUMBER ---
            if ch.isdigit():
                num = ''
                while self.pos < len(self.source) and self._peek() is not None and self._peek().isdigit():
                    num += self._advance()

                # Panic Mode: check for invalid numbers (attached letters or leading zeros)
                is_invalid = False
                if self.pos < len(self.source) and self._peek() is not None and self._peek().isalpha():
                    is_invalid = True
                elif len(num) > 1 and num.startswith('0'):
                    is_invalid = True

                if is_invalid:
                    bad = num
                    # For numbers, ONLY consume alphanumeric characters/underscores (e.g., stops at '!')
                    while self.pos < len(self.source) and self._peek() is not None and (
                            self._peek().isalnum() or self._peek() == '_'):
                        bad += self._advance()
                    self._add_error(start_lineno, bad, 'Invalid number')
                    continue
                return (start_lineno, 'NUM', num)

            # --- IDENTIFIER / KEYWORD ---
            if ch.isalpha():
                ident = ''
                while self.pos < len(self.source) and self._peek() is not None and (
                        self._peek().isalnum() or self._peek() == '_'):
                    ident += self._advance()

                # Panic Mode: consume invalid characters attached to identifiers
                if self.pos < len(
                        self.source) and self._peek() is not None and not self._peek().isspace() and self._peek() not in SINGLE_SYMBOLS and self._peek() != '=':
                    bad = ident
                    # Consumes until whitespace or symbol
                    while self.pos < len(
                            self.source) and self._peek() is not None and not self._peek().isspace() and self._peek() not in SINGLE_SYMBOLS and self._peek() != '=':
                        bad += self._advance()
                    self._add_error(start_lineno, bad, 'Invalid input')
                    continue

                if ident in KEYWORDS:
                    return (start_lineno, 'KEYWORD', ident)
                self._add_symbol(ident)
                return (start_lineno, 'ID', ident)

            # --- == (check before single =) ---
            if ch == '=' and self._peek(1) == '=':
                self._advance()
                self._advance()
                return (start_lineno, 'SYMBOL', '==')

            # --- SINGLE-CHARACTER SYMBOLS ---
            if ch in SINGLE_SYMBOLS:
                self._advance()
                return (start_lineno, 'SYMBOL', ch)

            # --- INVALID INPUT (catch-all) ---
            # Standalone invalid characters are evaluated one by one
            bad = self._advance()
            self._add_error(start_lineno, bad, 'Invalid input')
            continue

        return None

    def tokenize(self):
        while True:
            result = self.get_next_token()
            if result is None:
                break
            line, ttype, tval = result
            self._add_token(line, ttype, tval)


def main():
    try:
        with open('input.txt', 'r', encoding='utf-8') as f:
            source = f.read()
    except Exception:
        with open('lexical_errors.txt', 'w', encoding='utf-8') as fe:
            fe.write('There is no lexical error.')
        return

    scanner = Scanner(source)
    scanner.tokenize()

    with open('tokens.txt', 'w', encoding='utf-8') as ft:
        for lineno in sorted(scanner.tokens.keys()):
            pairs = ' '.join(f'({t}, {v})' for t, v in scanner.tokens[lineno])
            ft.write(f'{lineno}.\t{pairs}\n')

    with open('lexical_errors.txt', 'w', encoding='utf-8') as fe:
        if scanner.errors:
            for lineno in sorted(scanner.errors.keys()):
                for string, msg in scanner.errors[lineno]:
                    fe.write(f'{lineno}.\t({string}, {msg})\n')
        else:
            fe.write('There is no lexical error.')

    with open('symbol_table.txt', 'w', encoding='utf-8') as fs:
        for i, lexeme in enumerate(scanner.symbol_table, 1):
            fs.write(f'{i}.\t{lexeme}\n')


if __name__ == '__main__':
    main()
