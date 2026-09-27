# Keyhan Masoudi 401106509
# Yousef Sadidi 401170597
# Reference: Compilers: Principles, Techniques, and Tools (Aho, Lam, Sethi, Ullman)
#            LL(1) parsing algorithm from course Lecture Note 5

# ==============================================================================
#  SCANNER
# ==============================================================================

KEYWORDS = {
    'break', 'else', 'for', 'if', 'int', 'return', 'void',
    'goto', 'switch', 'case', 'default', 'while'
}
SINGLE_SYMBOLS = set(';:,[](){}+-*/=<')


class Scanner:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.lineno = 1

    def _peek(self, offset=0):
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else None

    def _advance(self):
        char = self.source[self.pos]
        self.pos += 1
        if char == '\n':
            self.lineno += 1
        return char

    def _skip_whitespace(self):
        skipped = False
        while self.pos < len(self.source) and self._peek() in {' ', '\n', '\r', '\t', '\v', '\f'}:
            skipped = True
            self._advance()
        return skipped

    def _scan_comment(self):
        if self._peek(1) == '*':
            self._advance(); self._advance()
            while self.pos < len(self.source):
                if self._peek() == '*' and self._peek(1) == '/':
                    self._advance(); self._advance()
                    return 'SKIP'
                self._advance()
            return 'SKIP'
        return None

    def _scan_number(self):
        start_lineno = self.lineno
        num = ''
        while self.pos < len(self.source) and self._peek().isdigit():
            num += self._advance()
        if self.pos < len(self.source) and self._peek().isalpha():
            while self.pos < len(self.source) and (self._peek().isalnum() or self._peek() == '_'):
                self._advance()
            return None
        return (start_lineno, 'NUM', num)

    def _scan_identifier(self):
        start_lineno = self.lineno
        ident = ''

        while self.pos < len(self.source) and self._peek().isalnum():
            ident += self._advance()

        if self.pos < len(self.source) and self._peek() == '_':
            self._advance()   # skip '_' and rescan the suffix as a new token
            return None

        if (self.pos < len(self.source)
                and not self._peek().isspace()
                and self._peek() not in SINGLE_SYMBOLS
                and self._peek() != '='):
            while (self.pos < len(self.source)
                   and not self._peek().isspace()
                   and self._peek() not in SINGLE_SYMBOLS
                   and self._peek() != '='):
                self._advance()
            return None

        if ident in KEYWORDS:
            return (start_lineno, 'KEYWORD', ident)
        return (start_lineno, 'ID', ident)

    def _scan_symbol(self, start_lineno):
        if self._peek() == '*' and self._peek(1) == '/':
            self._advance(); self._advance()
            return 'SKIP'
        if self._peek() in SINGLE_SYMBOLS:
            symbol = self._advance()
            return (start_lineno, 'SYMBOL', symbol)
        return None

    def get_next_token(self):
        while self.pos < len(self.source):
            if self._skip_whitespace():
                continue
            char = self._peek()
            if char is None:
                break
            start_lineno = self.lineno

            if char == '/':
                result = self._scan_comment()
                if result == 'SKIP':
                    continue
            if self.pos >= len(self.source):
                break
            char = self._peek()
            if char is None:
                break

            if char.isdigit():
                result = self._scan_number()
                if result is not None:
                    return result
                continue

            if char.isalpha():
                result = self._scan_identifier()
                if result is not None:
                    return result
                continue

            if char == '=' and self._peek(1) == '=':
                self._advance(); self._advance()
                return (start_lineno, 'SYMBOL', '==')

            result = self._scan_symbol(start_lineno)
            if result == 'SKIP':
                continue
            if result is not None:
                return result

            self._advance()

        return (self.lineno + 1, '$', '$')


# ==============================================================================
#  GRAMMAR HELPERS
# ==============================================================================

def kw(w):  return ('KEYWORD', w)
def sym(s): return ('SYMBOL', s)

ID  = ('ID',  None)
NUM = ('NUM', None)
EOF = ('$',   '$')
EPS = 'EPSILON'

# NTs that silently derive epsilon (direct or transitive EPSILON production).
# These produce epsilon quietly when no production matches but token in FOLLOW.
# Non-nullable NTs emit "missing <NT>" in that case.
SILENTLY_NULLABLE = frozenset([
    'AdditiveExpressionPrime', 'ArgListPrime', 'Args', 'C', 'CaseList', 'D',
    'DeclarationList', 'DefaultOpt', 'ElseOpt', 'FactorPrime', 'G',
    'ParamList', 'ParamPrime', 'SignedFactorPrime', 'SimpleExpressionPrime',
    'StatementList', 'TermPrime', 'VarPrime',
])

# ==============================================================================
#  GRAMMAR RULES
# ==============================================================================

GRAMMAR_RULES = {
    'Program':                  [['DeclarationList']],
    'DeclarationList':          [['Declaration', 'DeclarationList'], [EPS]],
    'Declaration':              [['DeclarationInitial', 'DeclarationPrime']],
    'DeclarationInitial':       [['TypeSpecifier', ID]],
    'DeclarationPrime':         [['FunDeclarationPrime'], ['VarDeclarationPrime']],
    'VarDeclarationPrime':      [[sym(';')],
                                 [sym('['), NUM, sym(']'), 'VarDeclArrayPrime'],
                                 [sym('='), 'Expression', sym(';')]],
    'VarDeclArrayPrime':        [[sym(';')], [sym('='), 'Expression', sym(';')]],
    'FunDeclarationPrime':      [[sym('('), 'Params', sym(')'), 'CompoundStmt']],
    'TypeSpecifier':            [[kw('int')], [kw('void')]],
    'Params':                   [[kw('int'), ID, 'ParamPrime', 'ParamList'], [kw('void')]],
    'ParamList':                [[sym(','), 'Param', 'ParamList'], [EPS]],
    'Param':                    [['DeclarationInitial', 'ParamPrime']],
    'ParamPrime':               [[sym('['), sym(']')], [EPS]],
    'CompoundStmt':             [[sym('{'), 'DeclarationList', 'StatementList', sym('}')]],
    'StatementList':            [['Statement', 'StatementList'], [EPS]],
    'Statement':                [[kw('if'), sym('('), 'Expression', sym(')'), 'Statement', 'ElseOpt'],
                                 ['OtherStmt']],
    'ElseOpt':                  [[kw('else'), 'Statement'], [EPS]],
    'OtherStmt':                [[ID, 'IdStatementPrime'],
                                 ['SimpleExpressionZegond', sym(';')],
                                 [sym(';')],
                                 ['CompoundStmt'],
                                 ['IterationStmt'],
                                 ['ReturnStmt'],
                                 ['BreakStmt'],
                                 ['GotoStmt'],
                                 ['SwitchStmt']],
    'IdStatementPrime':         [[sym(':'), 'Statement'], ['B', sym(';')]],
    'BreakStmt':                [[kw('break'), sym(';')]],
    'IterationStmt':            [[kw('while'), sym('('), 'Expression', sym(')'), 'Statement']],
    'ReturnStmt':               [[kw('return'), 'ReturnStmtPrime']],
    'ReturnStmtPrime':          [[sym(';')], ['Expression', sym(';')]],
    'Expression':               [['SimpleExpressionZegond'], [ID, 'B']],
    'B':                        [[sym('='), 'Expression'],
                                 [sym('['), 'Expression', sym(']'), 'H'],
                                 ['SimpleExpressionPrime']],
    'H':                        [[sym('='), 'Expression'], ['G', 'D', 'C']],
    'SimpleExpressionZegond':   [['AdditiveExpressionZegond', 'C']],
    'SimpleExpressionPrime':    [['AdditiveExpressionPrime', 'C']],
    'C':                        [['Relop', 'AdditiveExpression'], [EPS]],
    'Relop':                    [[sym('<')], [sym('==')]],
    'AdditiveExpression':       [['Term', 'D']],
    'AdditiveExpressionPrime':  [['TermPrime', 'D']],
    'AdditiveExpressionZegond': [['TermZegond', 'D']],
    'D':                        [['Addop', 'Term', 'D'], [EPS]],
    'Addop':                    [[sym('+')], [sym('-')]],
    'Term':                     [['SignedFactor', 'G']],
    'TermPrime':                [['SignedFactorPrime', 'G']],
    'TermZegond':               [['SignedFactorZegond', 'G']],
    'G':                        [['Mulop', 'SignedFactor', 'G'], [EPS]],
    'Mulop':                    [[sym('*')], [sym('/')]],
    'SignedFactor':             [[sym('+'), 'Factor'], [sym('-'), 'Factor'], ['Factor']],
    'SignedFactorPrime':        [['FactorPrime']],
    'SignedFactorZegond':       [[sym('+'), 'Factor'], [sym('-'), 'Factor'], ['FactorZegond']],
    'Factor':                   [[sym('('), 'Expression', sym(')')],
                                 [ID, 'VarCallPrime'],
                                 [NUM]],
    'VarCallPrime':             [[sym('('), 'Args', sym(')')], ['VarPrime']],
    'VarPrime':                 [[sym('['), 'Expression', sym(']')], [EPS]],
    'FactorPrime':              [[sym('('), 'Args', sym(')')], [EPS]],
    'FactorZegond':             [[sym('('), 'Expression', sym(')')], [NUM]],
    'Args':                     [['ArgList'], [EPS]],
    'ArgList':                  [['Expression', 'ArgListPrime']],
    'ArgListPrime':             [[sym(','), 'Expression', 'ArgListPrime'], [EPS]],
    'GotoStmt':                 [[kw('goto'), ID, sym(';')]],
    'SwitchStmt':               [[kw('switch'), sym('('), 'Expression', sym(')'),
                                   sym('{'), 'CaseList', 'DefaultOpt', sym('}')]],
    'CaseList':                 [['Case', 'CaseList'], [EPS]],
    'Case':                     [[kw('case'), 'Constant', sym(':'), 'StatementList']],
    'Constant':                 [[NUM]],
    'DefaultOpt':               [[kw('default'), sym(':'), 'StatementList'], [EPS]],
}

# ==============================================================================
#  FIRST / FOLLOW SETS
# ==============================================================================

_EXPR_FOLLOW = frozenset([sym(';'), sym(')'), sym(']'), sym(',')])
_RELOP       = frozenset([sym('<'), sym('==')])
_ADDOP       = frozenset([sym('+'), sym('-')])
_MULOP       = frozenset([sym('*'), sym('/')])
_ARITH_OPS   = _RELOP | _ADDOP | _MULOP
_STMT_FIRST  = frozenset([kw('if'), ID, sym('('), NUM, sym(';'), sym('{'),
                           kw('while'), kw('return'), kw('break'), kw('goto'),
                           kw('switch'), sym('+'), sym('-')])
_DECL_FIRST  = frozenset([kw('int'), kw('void')])
# IMPORTANT: _DECL_LIST_FOLLOW must include _DECL_FIRST because after any
# Declaration the next token can be 'int' or 'void' starting another Declaration.
_DECL_LIST_FOLLOW = _DECL_FIRST | _STMT_FIRST | frozenset([EOF, sym('}')])

FIRST = {
    'Program':                  _DECL_FIRST,
    'DeclarationList':          _DECL_FIRST | {EPS},
    'Declaration':              _DECL_FIRST,
    'DeclarationInitial':       _DECL_FIRST,
    'DeclarationPrime':         frozenset([sym('('), sym(';'), sym('['), sym('=')]),
    'VarDeclarationPrime':      frozenset([sym(';'), sym('['), sym('=')]),
    'VarDeclArrayPrime':        frozenset([sym(';'), sym('=')]),
    'FunDeclarationPrime':      frozenset([sym('(')]),
    'TypeSpecifier':            _DECL_FIRST,
    'Params':                   _DECL_FIRST,
    'ParamList':                frozenset([sym(','), EPS]),
    'Param':                    _DECL_FIRST,
    'ParamPrime':               frozenset([sym('['), EPS]),
    'CompoundStmt':             frozenset([sym('{')]),
    'StatementList':            _STMT_FIRST | {EPS},
    'Statement':                _STMT_FIRST,
    'ElseOpt':                  frozenset([kw('else'), EPS]),
    'OtherStmt':                _STMT_FIRST,
    'IdStatementPrime':         frozenset([sym(':'), sym('='), sym('['), sym('(')]) | _ARITH_OPS | frozenset([sym(';')]),
    'BreakStmt':                frozenset([kw('break')]),
    'IterationStmt':            frozenset([kw('while')]),
    'ReturnStmt':               frozenset([kw('return')]),
    'ReturnStmtPrime':          frozenset([sym(';'), ID, sym('('), NUM]) | _ADDOP,
    'Expression':               frozenset([ID, sym('('), NUM]) | _ADDOP,
    'B':                        frozenset([sym('='), sym('['), sym('('), sym(';')]) | _ARITH_OPS,
    'H':                        frozenset([sym('=')]) | _ARITH_OPS,
    'SimpleExpressionZegond':   frozenset([sym('('), NUM]) | _ADDOP,
    'SimpleExpressionPrime':    frozenset([sym('(')]) | _ARITH_OPS | {EPS},
    'C':                        _RELOP | {EPS},
    'Relop':                    _RELOP,
    'AdditiveExpression':       frozenset([ID, sym('('), NUM]) | _ADDOP,
    'AdditiveExpressionPrime':  frozenset([sym('(')]) | _MULOP | _ADDOP | {EPS},
    'AdditiveExpressionZegond': frozenset([sym('('), NUM]) | _ADDOP,
    'D':                        _ADDOP | {EPS},
    'Addop':                    _ADDOP,
    'Term':                     frozenset([ID, sym('('), NUM]) | _ADDOP,
    'TermPrime':                frozenset([sym('(')]) | _MULOP | {EPS},
    'TermZegond':               frozenset([sym('('), NUM]) | _ADDOP,
    'G':                        _MULOP | {EPS},
    'Mulop':                    _MULOP,
    'SignedFactor':             frozenset([ID, sym('('), NUM]) | _ADDOP,
    'SignedFactorPrime':        frozenset([sym('('), EPS]),
    'SignedFactorZegond':       frozenset([sym('('), NUM]) | _ADDOP,
    'Factor':                   frozenset([ID, sym('('), NUM]),
    'VarCallPrime':             frozenset([sym('('), sym('[')]) | _ARITH_OPS | _EXPR_FOLLOW | {EPS},
    'VarPrime':                 frozenset([sym('['), EPS]),
    'FactorPrime':              frozenset([sym('('), EPS]),
    'FactorZegond':             frozenset([sym('('), NUM]),
    'Args':                     frozenset([ID, sym('('), NUM]) | _ADDOP | {EPS},
    'ArgList':                  frozenset([ID, sym('('), NUM]) | _ADDOP,
    'ArgListPrime':             frozenset([sym(','), EPS]),
    'GotoStmt':                 frozenset([kw('goto')]),
    'SwitchStmt':               frozenset([kw('switch')]),
    'CaseList':                 frozenset([kw('case'), EPS]),
    'Case':                     frozenset([kw('case')]),
    'Constant':                 frozenset([NUM]),
    'DefaultOpt':               frozenset([kw('default'), EPS]),
}

_STMT_CTX_FOLLOW = _DECL_LIST_FOLLOW | frozenset([kw('else')])

FOLLOW = {
    'Program':                  frozenset([EOF]),
    'DeclarationList':          _DECL_LIST_FOLLOW,
    'Declaration':              _DECL_LIST_FOLLOW,
    'DeclarationInitial':       frozenset([sym('('), sym(';'), sym('['), sym('='), sym(','), sym(']')]),
    'DeclarationPrime':         _DECL_LIST_FOLLOW,
    'VarDeclarationPrime':      _DECL_LIST_FOLLOW,
    'VarDeclArrayPrime':        _DECL_LIST_FOLLOW,
    'FunDeclarationPrime':      _DECL_LIST_FOLLOW,
    'TypeSpecifier':            frozenset([ID]),
    'Params':                   frozenset([sym(')')]),
    'ParamList':                frozenset([sym(')')]),
    'Param':                    frozenset([sym(','), sym(')')]),
    'ParamPrime':               frozenset([sym(','), sym(')')]),
    'CompoundStmt':             _STMT_CTX_FOLLOW,
    'StatementList':            frozenset([sym('}'), kw('case'), kw('default')]),
    'Statement':                _STMT_CTX_FOLLOW,
    'ElseOpt':                  _STMT_CTX_FOLLOW,
    'OtherStmt':                _STMT_CTX_FOLLOW,
    'IdStatementPrime':         _STMT_CTX_FOLLOW,
    'BreakStmt':                _STMT_CTX_FOLLOW,
    'IterationStmt':            _STMT_CTX_FOLLOW,
    'ReturnStmt':               _STMT_CTX_FOLLOW,
    'ReturnStmtPrime':          _STMT_CTX_FOLLOW,
    'Expression':               _EXPR_FOLLOW,
    'B':                        _EXPR_FOLLOW,
    'H':                        _EXPR_FOLLOW,
    'SimpleExpressionZegond':   _EXPR_FOLLOW,
    'SimpleExpressionPrime':    _EXPR_FOLLOW,
    'C':                        _EXPR_FOLLOW,
    'Relop':                    frozenset([ID, sym('('), NUM]) | _ADDOP,
    'AdditiveExpression':       _RELOP | _EXPR_FOLLOW,
    'AdditiveExpressionPrime':  _RELOP | _EXPR_FOLLOW,
    'AdditiveExpressionZegond': _RELOP | _EXPR_FOLLOW,
    'D':                        _RELOP | _EXPR_FOLLOW,
    'Addop':                    frozenset([ID, sym('('), NUM]) | _ADDOP,
    'Term':                     _ADDOP | _RELOP | _EXPR_FOLLOW,
    'TermPrime':                _ADDOP | _RELOP | _EXPR_FOLLOW,
    'TermZegond':               _ADDOP | _RELOP | _EXPR_FOLLOW,
    'G':                        _ADDOP | _RELOP | _EXPR_FOLLOW,
    'Mulop':                    frozenset([ID, sym('('), NUM]) | _ADDOP,
    'SignedFactor':             _MULOP | _ADDOP | _RELOP | _EXPR_FOLLOW,
    'SignedFactorPrime':        _MULOP | _ADDOP | _RELOP | _EXPR_FOLLOW,
    'SignedFactorZegond':       _MULOP | _ADDOP | _RELOP | _EXPR_FOLLOW,
    'Factor':                   _MULOP | _ADDOP | _RELOP | _EXPR_FOLLOW,
    'VarCallPrime':             _MULOP | _ADDOP | _RELOP | _EXPR_FOLLOW,
    'VarPrime':                 _MULOP | _ADDOP | _RELOP | _EXPR_FOLLOW,
    'FactorPrime':              _MULOP | _ADDOP | _RELOP | _EXPR_FOLLOW,
    'FactorZegond':             _MULOP | _ADDOP | _RELOP | _EXPR_FOLLOW,
    'Args':                     frozenset([sym(')')]),
    'ArgList':                  frozenset([sym(')')]),
    'ArgListPrime':             frozenset([sym(')')]),
    'GotoStmt':                 _STMT_CTX_FOLLOW,
    'SwitchStmt':               _STMT_CTX_FOLLOW,
    'CaseList':                 frozenset([kw('default'), sym('}')]),
    'Case':                     frozenset([kw('case'), kw('default'), sym('}')]),
    'Constant':                 frozenset([sym(':')]),
    'DefaultOpt':               frozenset([sym('}')]),
}


# ==============================================================================
#  BUILD PARSE TABLE
# ==============================================================================

def _build_table():
    table = {}
    for nt, prods in GRAMMAR_RULES.items():
        table[nt] = {}
        for prod in prods:
            predict = set()
            all_nullable = True
            for item in prod:
                if item == EPS:
                    break
                if isinstance(item, str):
                    f = FIRST.get(item, set())
                    predict |= (f - {EPS})
                    if EPS not in f:
                        all_nullable = False
                        break
                else:
                    predict.add(item)
                    all_nullable = False
                    break
            if all_nullable:
                predict |= FOLLOW.get(nt, frozenset())
            for terminal in predict:
                if terminal != EPS:
                    if terminal not in table[nt]:
                        table[nt][terminal] = prod
    return table


PARSE_TABLE = _build_table()


# ==============================================================================
#  PARSE TREE NODE
# ==============================================================================

class Node:
    def __init__(self, label):
        self.label = label
        self.children = []

    def add_child(self, child):
        self.children.append(child)


# ==============================================================================
#  TREE RENDERING  (box-drawing characters: ├── └── │   )
# ==============================================================================

def write_tree(root, lines):
    # Skip root completely only if label is None (should not happen for Program)
    if root.label is None:
        return
    lines.append(root.label)

    # Filter children with real labels
    visible_children = [c for c in root.children if c.label is not None]
    for i, child in enumerate(visible_children):
        _render(child, lines, '', i == len(visible_children) - 1)

def _render(node, lines, prefix, is_last):
    if node.label is None:
        return

    connector = '\u2514\u2500\u2500 ' if is_last else '\u251c\u2500\u2500 '
    lines.append(prefix + connector + node.label)

    extension = '    ' if is_last else '\u2502   '
    visible_children = [c for c in node.children if c.label is not None]
    for i, child in enumerate(visible_children):
        _render(child, lines, prefix + extension,
                i == len(visible_children) - 1)


# ==============================================================================
#  TOKEN HELPERS
# ==============================================================================

def _token_to_key(tok):
    _, ttype, tval = tok
    if ttype == 'KEYWORD':  return ('KEYWORD', tval)
    if ttype == 'ID':       return ('ID', None)
    if ttype == 'NUM':      return ('NUM', None)
    if ttype == 'SYMBOL':   return ('SYMBOL', tval)
    if ttype == '$':        return ('$', '$')
    return (ttype, tval)


def _terminal_label(tok):
    _, ttype, tval = tok
    if ttype == 'KEYWORD':  return f'(KEYWORD, {tval}) '
    if ttype == 'ID':       return f'(ID, {tval}) '
    if ttype == 'NUM':      return f'(NUM, {tval}) '
    if ttype == 'SYMBOL':     return f'(SYMBOL, {tval}) '
    if ttype == '$':        return '$ '
    return f'({ttype}, {tval})'


def _error_token_str(tok):
    """Return type name for ID/NUM; literal value for keywords and symbols."""
    _, ttype, tval = tok
    if ttype == 'ID':      return 'ID'
    if ttype == 'NUM':     return 'NUM'
    if ttype == 'KEYWORD': return tval
    if ttype == 'SYMBOL':  return tval
    if ttype == '$':       return 'EOF'
    return tval


# ==============================================================================
#  PARSER  (LL(1) predictive, panic-mode error recovery)
# ==============================================================================

RECOVERY_FALLBACK = {
    'B': ['SimpleExpressionPrime'],
    'H': ['G', 'D', 'C'],
}

class Parser:
    def __init__(self, scanner):
        self.scanner = scanner
        self.errors = []
        self.current_token = None
        self._advance()

    def _advance(self):
        self.current_token = self.scanner.get_next_token()

    def _cur_key(self):
        return _token_to_key(self.current_token)

    def _cur_lineno(self):
        return self.current_token[0]

    def parse(self):
        root = Node('Program')
        self._parse_nt('Program', root)
        # ($) is always the last child of Program
        root.add_child(Node('$'))
        return root

    def _parse_nt(self, nt, node):
        key = self._cur_key()
        prod = PARSE_TABLE.get(nt, {}).get(key)

        if prod is None:
            follow = FOLLOW.get(nt, frozenset())
            if key == EOF:
                self.errors.append(f'#{self._cur_lineno()} : syntax error, missing {nt}')
                node.label = None
                return
            if key in follow:
                if nt not in SILENTLY_NULLABLE:
                    self.errors.append(
                        f'#{self._cur_lineno()} : syntax error, missing {nt}'
                    )
                    node.label = None
                    return
                node.add_child(Node('epsilon'))
                return

            self.errors.append(
                f'#{self._cur_lineno()} : syntax error, illegal {_error_token_str(self.current_token)}'
            )
            self._advance()

            first_nt = FIRST.get(nt, set()) - {EPS}
            sync = follow | first_nt
            while self._cur_key() not in sync and self._cur_key() != EOF:
                self.errors.append(
                    f'#{self._cur_lineno()} : syntax error, illegal {_error_token_str(self.current_token)}'
                )
                self._advance()

            if self._cur_key() in first_nt:
                prod2 = PARSE_TABLE.get(nt, {}).get(self._cur_key())
                if prod2 is not None:
                    self._expand(nt, prod2, node)
                    return

            fallback = RECOVERY_FALLBACK.get(nt)
            if fallback is not None and self._cur_key() in follow:
                self._expand(nt, fallback, node)
                return

            # If error recovery consumed illegal tokens and landed at EOF,
            # the NT was never parsed — report it as missing.
            if self._cur_key() == EOF:
                self.errors.append(f'#{self._cur_lineno()} : syntax error, missing {nt}')
            node.label = None
            return

        self._expand(nt, prod, node)

    def _expand(self, nt, prod, node):
        if prod == [EPS]:
            node.add_child(Node('epsilon'))
            return

        # Create child nodes first, then fill them in left-to-right
        child_nodes = []
        for item in prod:
            if item == EPS:
                child_nodes.append(Node('epsilon'))
            elif isinstance(item, str):
                child_nodes.append(Node(item))
            else:
                child_nodes.append(Node(None))
        for cn in child_nodes:
            node.add_child(cn)

        for i, item in enumerate(prod):
            if item == EPS:
                continue
            elif isinstance(item, str):
                self._parse_nt(item, child_nodes[i])
                # IMPORTANT for T10: if a child becomes None but its NT was natively nullable 
                # or safely skipped, we should revert it to epsilon if it was supposed to be in a list
                if child_nodes[i].label is None and item in SILENTLY_NULLABLE and self._cur_key() != EOF:
                    child_nodes[i].label = item
                    child_nodes[i].add_child(Node('epsilon'))
            else:
                # Terminal match
                if self._cur_key() == item:
                    child_nodes[i].label = _terminal_label(self.current_token)
                    self._advance()
                else:
                    lineno = self._cur_lineno()
                    exp_type, exp_val = item
                    
                    exp_str = exp_val if exp_val else exp_type
                    self.errors.append(f'#{lineno} : syntax error, missing {exp_str}')

                    # Mark this child as to-be-hidden in the tree
                    child_nodes[i].label = None

# ==============================================================================
#  MAIN
# ==============================================================================

def main():
    try:
        with open('input.txt', 'r', encoding='utf-8') as f:
            source = f.read()
    except Exception:
        with open('parse_tree.txt', 'w', encoding='utf-8') as fp:
            fp.write('')
        with open('syntax_errors.txt', 'w', encoding='utf-8') as fe:
            fe.write('There is no syntax error.')
        return

    scanner = Scanner(source)
    parser = Parser(scanner)
    root = parser.parse()

    lines = []
    write_tree(root, lines)
    with open('parse_tree.txt', 'w', encoding='utf-8') as fp:
        fp.write('\n'.join(lines) + '\n')

    with open('syntax_errors.txt', 'w', encoding='utf-8') as fe:
        if parser.errors:
            fe.write('\n'.join(parser.errors) + '\n')
        else:
            fe.write('There is no syntax error.')


if __name__ == '__main__':
    main()
