##############################################
#            IMPORTS
##############################################

from string_with_arrows import string_with_arrows


##############################################
#            CONSTANTS
##############################################

DIGITS = '0123456789'

##############################################
#            ERROR HANDLING
##############################################

class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self):
        result = f'ERROR: {self.error_name}: {self.details}\n'
        result += f'File: {self.pos_start.fn}, Line: {self.pos_start.ln + 1}'
        result += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)

class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Invalid Syntax', details)

##############################################
#               POSITION
##############################################

class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1

        if current_char == "\n":
            self.ln += 1
            self.col = 0

        return self
    
    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)


##############################################
#               TOKENS
##############################################


ST_INT = 'INT'
ST_FLOAT = 'FLOAT'
ST_PLUS = 'PLUS'
ST_MINUS = 'MINUS'
ST_MUL = 'MUL'
ST_DIV = 'DIV'
ST_LPAREN = 'LPAREN'
ST_RPAREN = 'RPAREN'
ST_EOF = 'EOF'

class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = self.pos_start.copy()
            self.pos_end.advance()

        if pos_end:
            self.pos_end = pos_end.copy()
        
    def __repr__(self):
        if self.value: return f'{self.type}:{self.value}'
        return f'{self.type}'
    
##############################################
#               LEXER
##############################################

class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.advance()
    
    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None
    
    def make_tokens(self):
        tokens = []

        while self.current_char != None:
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char == '+':
                tokens.append(Token(ST_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(ST_MINUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(ST_MUL, pos_start=self.pos))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(ST_DIV, pos_start=self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(ST_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(ST_RPAREN, pos_start=self.pos))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")
            
        tokens.append(Token(ST_EOF, pos_start=self.pos))
        return tokens, None
    
    def make_number(self):
        num_str = ''
        dot_count = 0
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.advance()
        if dot_count == 0:
            return Token(ST_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(ST_FLOAT, float(num_str), pos_start, self.pos)

##############################################
#               NODES
##############################################

class NumberNode:
    def __init__(self, tok):
        self.tok = tok

    def __repr__(self):
        return f'{self.tok}'

class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node

    def __repr__(self):
        return f'({self.left_node}, {self.op_tok}, {self.right_node})'
    
class UnaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node

    def __repr__(self):
        return f'({self.op_tok}, {self.node})'

##############################################
#               PARSE RESULT
##############################################

class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None

    def register(self, res):
        if isinstance(res, ParseResult):
            if res.error: self.error = res.error
            return res.node
        
        return res

    def success(self, node):
        self.node = node
        return self

    def failiure(self, error):
        self.error = error
        return self

##############################################
#               PARSER
##############################################

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.advance()
    
    def advance(self,):
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
            return self.current_tok

###################################################

    def parse(self):
        res = self.expr()
        if not res.error and self.current_tok.type != ST_EOF: 
            return res.failiure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected a valid operator: '+', '-', '*' or '/' "
            ))
        return res        

    def factor(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (ST_PLUS, ST_MINUS):
            res.register(self.advance())
            factor = res.register(self.factor())
            if res.error: return res
            return res.success(UnaryOpNode(tok, factor))

        elif tok.type in (ST_INT, ST_FLOAT):
            res.register(self.advance())
            return res.success(NumberNode(tok))
        
        elif tok.type == ST_LPAREN:
            res.register(self.advance())
            expr = res.register(self.expr())
            if res.error: return res
            if self.current_tok.type == ST_RPAREN:
                res.register(self.advance())
                return res.success(expr)
            else:
                return res.failiure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected a closing bracket ')'"
                ))
        
        return res.failiure(InvalidSyntaxError(
            tok.pos_start, tok.pos_end,
            "Expected an Integer or a Float"
        ))

    def term(self):
        return self.bin_op(self.factor, (ST_MUL,ST_DIV))

    def expr(self):
        return self.bin_op(self.term, (ST_PLUS,ST_MINUS))
    
    def bin_op(self, func, ops):
        res = ParseResult()
        left = res.register(func())
        if res.error: return res

        while self.current_tok.type in ops:
            op_tok = self.current_tok
            res.register(self.advance())
            right = res.register(func())
            if res.error: return res
            left = BinOpNode(left, op_tok, right)

        return res.success(left)

##############################################
#               VALUES
##############################################

class Number:
    def __init__(self):
        pass

##############################################
#               INTERPRETER
##############################################

class Interpreter:
    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit_method)
        return method(node)

    def no_visit_method(self, node):
        raise Exception(f'NO VISIT METHOD DEFINED!!! {type(node).__name__}')

    def visit_NumberNode(self, node):
        print("Num Node")

    def visit_BinOpNode(self, node):
        print("BinOp Node")
        self.visit(node.left_node)
        self.visit(node.right_node)

    def visit_UnaryOpNode(self, node):
        print("UnuaryOp Node")
        self.visit(node.node)
##############################################
#               RUN
##############################################

def run(fn, text):
    # Gen Tokens
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error: return None, error

    # Gen AST
    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error: return None, ast.error
    #Run
    interpreter = Interpreter()
    interpreter.visit(ast.node)
    return None,None
    #return ast.node, ast.error

  #  return ast, None

   # return tokens, error