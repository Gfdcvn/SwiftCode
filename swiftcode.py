##############################################
#            IMPORTS
##############################################

from string_with_arrows import string_with_arrows
import string

##############################################
#            CONSTANTS
##############################################

DIGITS = '0123456789'
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS


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
class ExpectedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Expected Character', details)
class RTError(Error):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, 'Runtime Error', details)
        self.context = context

    def as_string(self):
        result = self.generate_traceback()
        result += f'ERROR: {self.error_name}: {self.details}\n'
        result += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

    def generate_traceback(self):
        result = ''
        pos = self.pos_start
        ctx = self.context

        while ctx:
            result += f'File: {pos.fn}, Line: {str(pos.ln + 1)}, in {ctx.display_name}\n' + result
            pos = ctx.parent_entry_pos
            ctx = ctx.parent

        return 'SwiftCode Traceback (most recent call last):\n' + result
    

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
ST_IDENTIFIER = 'IDENTIFIER'
ST_KEYWORD = 'KEYWORD'
ST_PLUS = 'PLUS'
ST_MINUS = 'MINUS'
ST_MUL = 'MUL'
ST_DIV = 'DIV'
ST_POW = 'POW'
ST_EQ = 'EQ'
ST_LPAREN = 'LPAREN'
ST_RPAREN = 'RPAREN'
ST_EE = 'EE'
ST_NE = 'NE'
ST_LT = 'LT'
ST_GT = 'GT'
ST_LTE = 'LTE'
ST_GTE = 'GTE'
ST_EOF = 'EOF'

KEYWORDS = [
    'variable', # Variable Declaration
    'and', # Logical
    'or', # Logical
    'not' # Logical
]

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
        
    def matches(self, type_, value):
        return self.type == type_ and self.value == value
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
            elif self.current_char in LETTERS:
                tokens.append(self.make_identifier())
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
            elif self.current_char == '^':
                tokens.append(Token(ST_POW, pos_start=self.pos))
                self.advance()

            elif self.current_char == '(':
                tokens.append(Token(ST_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(ST_RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == '!':
                tok, error = self.make_not_equals()
                if error: return [], error
                tokens.append(tok)
            elif self.current_char == '=':
                tokens.append(self.make_equals())
            elif self.current_char == '<':
                tokens.append(self.make_less_than())
            elif self.current_char == '>':
                tokens.append(self.make_greater_than())
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
        
    def make_identifier(self):
        id_str = ''
        pos_start = self.pos.copy()
        while self.current_char != None and self.current_char in LETTERS_DIGITS + '_':
            id_str += self.current_char
            self.advance()

        tok_type = ST_KEYWORD if id_str in KEYWORDS else ST_IDENTIFIER
        return Token(tok_type, id_str, pos_start, self.pos)
    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            return Token(ST_NE, pos_start=pos_start, pos_end=self.pos), None
        self.advance()
        return None, ExpectedCharError(pos_start, self.pos, "'=' after '!'")
    
    def make_equals(self):
        tok_type = ST_EQ
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = ST_EE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)
    def make_less_than(self):
        tok_type = ST_LT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = ST_LTE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)
    def make_greater_than(self):
        tok_type = ST_GT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = ST_GTE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)


##############################################
#               NODES
##############################################

class NumberNode:
    def __init__(self, tok):
        self.tok = tok

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self):
        return f'{self.tok}'
    
class VarAccessNode:
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok
        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.var_name_tok.pos_end

class VarAssignNode:
    def __init__(self, var_name_tok, value_node):
        self.var_name_tok = var_name_tok
        self.value_node = value_node
        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.value_node.pos_end

class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node

        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self):
        return f'({self.left_node}, {self.op_tok}, {self.right_node})'
    
class UnaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node

        self.pos_start = self.op_tok.pos_start
        self.pos_end = node.pos_end

    def __repr__(self):
        return f'({self.op_tok}, {self.node})'

##############################################
#               PARSE RESULT
##############################################

class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None

    def register_advancment(self):
        pass

    def register(self, res):
        if res.error: self.error = res.error
        return res.node


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
                "Expected a valid operator: '+', '-', '*', '^' or '/'. Got an invalid operator instead! "
            ))
        return res        
######################################################

    def atom(self):
        res = ParseResult()
        tok = self.current_tok
        if tok.type in (ST_INT, ST_FLOAT):
            res.register_advancment()
            self.advance()
            return res.success(NumberNode(tok))
        
        elif tok.type == ST_IDENTIFIER:
            res.register_advancment()
            self.advance()
            return res.success(VarAccessNode(tok))
        
        elif tok.type == ST_LPAREN:
            res.register_advancment()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            if self.current_tok.type == ST_RPAREN:
                res.register_advancment()
                self.advance()
                return res.success(expr)
            else:
                return res.failiure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected a closing bracket ')'"
                ))
        
        return res.failiure(InvalidSyntaxError(
            tok.pos_start, tok.pos_end,
            "Expected an int, a float, an identifier, '+', '-' or '('"
        ))
    
    def power(self):
        return self.bin_op(self.atom, (ST_POW, ), self.factor)
        
   
    def factor(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (ST_PLUS, ST_MINUS):
            res.register_advancment()
            self.advance()
            factor = res.register(self.factor())
            if res.error: return res
            return res.success(UnaryOpNode(tok, factor))


        return self.power()

    def term(self):
        return self.bin_op(self.factor, (ST_MUL,ST_DIV))
    
    def arith_expr(self):
        return self.bin_op(self.term, (ST_PLUS, ST_MINUS))

    def comp_expr(self):
        res = ParseResult()

        if self.current_tok.matches(ST_KEYWORD, 'not'):
            op_tok = self.current_tok
            res.register_advancment()
            self.advance()

            node = res.register(self.comp_expr())
            if res.error: return res
            return res.success(UnaryOpNode(op_tok, node))
        node = res.register(self.bin_op(self.arith_expr, ((ST_EE, ST_NE, ST_LT, ST_GT, ST_LTE, ST_GTE))))

        if res.error:
            return res.failiure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected an int, a float, an identifier, '+', '-', '(', 'not'"
            ))
        return res.success(node)

    def expr(self):
        res = ParseResult()
        if self.current_tok.matches(ST_KEYWORD, 'variable'):
            res.register_advancment()
            self.advance()
            if self.current_tok.type != ST_IDENTIFIER:
                return res.failiure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    'Expected identifier after variable declaration'
                )) 
            var_name = self.current_tok
            res.register_advancment()
            self.advance()

            if self.current_tok.type != ST_EQ:
                return res.failiure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '=' after variable name"
                ))
            
            res.register_advancment()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            return res.success(VarAssignNode(var_name, expr))


        node =  res.register(self.bin_op(self.comp_expr, ((ST_KEYWORD, 'and'), (ST_KEYWORD, 'or'))))

        if res.error: 
            return res.failiure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'variable', an integer, a float, an identifier, '+', '-' or '('"
            ))
        return res.success(node)
    
    def bin_op(self, func_a, ops, func_b=None):
        if func_b == None:
            func_b = func_a
        res = ParseResult()
        left = res.register(func_a())
        if res.error: return res

        while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops: 
            op_tok = self.current_tok
            res.register_advancment()
            self.advance()
            right = res.register(func_b())
            if res.error: return res
            left = BinOpNode(left, op_tok, right)

        return res.success(left)

##############################################
#               RT RESULT
##############################################

class RTResult:
    def __init__(self):
        self.value = None
        self.error = None
        self.advance_count = 0

    def register_advancement(self):
        self.advance_count += 1
    
    def register(self, res):
        self.advance_count += res.advance_count
        if res.error: self.error = res.error
        return res.value
    def success(self, value):
        self.value = value
        return self
    
    def failiure(self, error):
        if not self.error or self.advance_count == 0:
            self.error = error
        return self

##############################################
#               VALUES
##############################################

class Number:
    def __init__(self, value):
        self.value = value
        self.set_pos() 
        self.set_context() 

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self
    def set_context(self, context=None):
        self.context = context
        return self
    def added_to(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None
    def subbed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        
    def multed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
    def dived_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(
                    other.pos_start, other.pos_end,
                    'Division by zero is not possible!',
                    self.context
                )
            return Number(self.value / other.value).set_context(self.context), None
        
    def powed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value ** other.value).set_context(self.context), None
        
    def get_comparison_eq(self, other):
        if isinstance(other, Number):
            return Number(int(self.value == other.value)).set_context(self.context), None
    def get_comparison_ne(self, other):
        if isinstance(other, Number):
            return Number(int(self.value != other.value)).set_context(self.context), None
    def get_comparison_lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value < other.value)).set_context(self.context), None
    def get_comparison_gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value > other.value)).set_context(self.context), None
    def get_comparison_lte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value <= other.value)).set_context(self.context), None
    def get_comparison_gte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value >= other.value)).set_context(self.context), None
    def anded_by(self, other):
        if isinstance(other, Number):
            return Number(int(self.value and other.value)).set_context(self.context), None
    def ored_by(self, other):
        if isinstance(other, Number):
            return Number(int(self.value or other.value)).set_context(self.context), None
    def notted(self):
        return Number(1 if self.value == 0 else 0).set_context(self.context), None

    def copy(self):
        copy = Number(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy
        
    def __repr__(self):
        return str(self.value)
    
##############################################
#               CONTEXT
##############################################

class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None

##############################################
#               SYMBOL TABLE
##############################################

class SymbolTable:
    def __init__(self):
        self.symbols = {}
        self.parent = None

    def get(self, name):
        value = self.symbols.get(name, None)
        if value == None and self.parent:
            return self.parent.get(name)
        return value
    
    def set(self, name, value):
        self.symbols[name] = value

    def remove(self, name):
        del self.symbols[name]

##############################################
#               INTERPRETER
##############################################

class Interpreter:
    def visit(self, node, context):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)

    def no_visit_method(self, node, context):
        raise Exception(f'NO VISIT METHOD DEFINED!!! {type(node).__name__}')

    def visit_NumberNode(self, node, context):
        return RTResult().success(
            Number(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
        )
    
    def visit_VarAccessNode(self, node, context):
        res = RTResult()
        var_name = node.var_name_tok.value
        value = context.symbol_table.get(var_name)

        if not value:
            return res.failiure(RTError(
                node.pos_start, node.pos_end,
                f"Variable '{var_name}' is not defined!!",
                context
            ))
        
        value = value.copy().set_pos(node.pos_start, node.pos_end)
        return res.success(value)
    
    def visit_VarAssignNode(self, node, context):
        res = RTResult()
        var_name = node.var_name_tok.value
        value = res.register(self.visit(node.value_node, context))
        if res.error: return res

        context.symbol_table.set(var_name, value)
        return res.success(value)

    def visit_BinOpNode(self, node, context):
        res = RTResult()
        left = res.register(self.visit(node.left_node, context))
        if res.error: return res
        right = res.register(self.visit(node.right_node, context))
        if res.error: return res

        if node.op_tok.type == ST_PLUS:
            result, error = left.added_to(right)
        elif node.op_tok.type == ST_MINUS:
            result, error = left.subbed_by(right)
        elif node.op_tok.type == ST_MUL:
            result, error = left.multed_by(right)
        elif node.op_tok.type == ST_DIV:
            result, error = left.dived_by(right)
        elif node.op_tok.type == ST_POW:
            result, error = left.powed_by(right)
        elif node.op_tok.type == ST_EE:
            result, error = left.get_comparison_eq(right)
        elif node.op_tok.type == ST_NE:
            result, error = left.get_comparison_ne(right)
        elif node.op_tok.type == ST_LT:
            result, error = left.get_comparison_lt(right)
        elif node.op_tok.type == ST_GT:
            result, error = left.get_comparison_gt(right)
        elif node.op_tok.type == ST_LTE:
            result, error = left.get_comparison_lte(right)
        elif node.op_tok.type == ST_GTE:
            result, error = left.get_comparison_gte(right)
        elif node.op_tok.matches(ST_KEYWORD, 'and'):
            result, error = left.anded_by(right)
        elif node.op_tok.matches(ST_KEYWORD, 'or'):
            result, error = left.ored_by(right)

        if error:
            return res.failiure(error)
        else:
            return res.success(result.set_pos(node.pos_start, node.pos_end))
    
    def visit_UnaryOpNode(self, node, context):
        res = RTResult()
        number = res.register(self.visit(node.node, context))
        if res.error: return res

        error = None

        if node.op_tok.type == ST_MINUS:
            number, error = number.multed_by(Number(-1))
        elif node.op_tok.matches(ST_KEYWORD, 'not'):
            number, error = number.notted()

        if res.error:
            return res.failiure(error)
        else:
            return res.success(number.set_pos(node.pos_start, node.pos_end))
##############################################
#               RUN
##############################################

global_symbol_table = SymbolTable()
global_symbol_table.set("null", Number(0))
global_symbol_table.set("true", Number(1))
global_symbol_table.set("false", Number(0))

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
    context = Context('<code>')
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)
    return result.value, result.error
