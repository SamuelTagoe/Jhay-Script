from string_with_arrow import *

###########################################
# CONSTANTS
###########################################

DIGITS = '0123456789'

###########################################
# ERRORS
###########################################

class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self):  # To create a str that would show the error name and details
        result = f'{self.error_name}: {self.details}\n'
        result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}'
        result += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

class IllegalCharError(Error):  # SubClass to Inherit from Error Class
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)

class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'Invalid Syntax', details)

###########################################
# POSITION
###########################################

class Position:
    def __init__(self, idx, ln, col, fn, ftxt):  # With a file name and file text
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char):  
        # To move on to the next index and then update the line and column num as well if necessary
        self.idx += 1
        self.col += 1

        if current_char == '\n':
            self.ln += 1
            self.col = 0

        return self
    
    def copy(self): 
        # To create a copy of the position
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)

###########################################
# TOKENS
###########################################

# Constants for different token types
TT_INT          = 'TT_INT'
TT_FLOAT        = 'TT_FLOAT'
TT_PLUS         = 'PLUS'
TT_MINUS        = 'MINUS'
TT_MUL          = 'MUL'
TT_DIV          = 'DIV'
TT_LPAREN       = 'LPAREN'
TT_RPAREN       = 'RPAREN'

class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()
        
        if pos_end:
            self.pos_end = pos_end

###########################################
# LEXER
###########################################

class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        if self.pos.idx < len(self.text):
            self.current_char = self.text[self.pos.idx]
        else:
            self.current_char = None

    def make_tokens(self):
        tokens = []

        while self.current_char is not None:  # Loop to go through every char of the text
            if self.current_char in ' \t':  # To ignore spaces and tabs
                self.advance()

            elif self.current_char in DIGITS:
                tokens.append(self.make_number())  # Create a number token

            elif self.current_char == '+':  
                tokens.append(Token(TT_PLUS))
                self.advance()
            elif self.current_char == '-':  
                tokens.append(Token(TT_MINUS))
                self.advance()
            elif self.current_char == '*':  
                tokens.append(Token(TT_MUL))
                self.advance()
            elif self.current_char == '/':  
                tokens.append(Token(TT_DIV))
                self.advance()
            elif self.current_char == '(':  
                tokens.append(Token(TT_LPAREN))
                self.advance()
            elif self.current_char == ')':  
                tokens.append(Token(TT_RPAREN))
                self.advance()

            else:  # Handle illegal character
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"Illegal character '{char}'")
            
        return tokens, None  # Return None if no error
    
    def make_number(self):
        num_str = ''
        dot_count = 0

        while self.current_char is not None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1:
                    break  # Only one dot is allowed in a number
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.advance()    

        if dot_count == 0:
            return Token(TT_INT, int(num_str))  # Return an integer token
        else:
            return Token(TT_FLOAT, float(num_str))  # Return a float token

###########################################
# NODES
###########################################

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

###########################################
# PASSER
###########################################

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1  # Start at -1 so the first advance() sets it to 0
        self.advance()

    def advance(self):
        self.tok_idx += 1

        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
        return self.current_tok

    def parse(self):
        return self.expr()

    def factor(self):
        tok = self.current_tok

        if tok.type in (TT_INT, TT_FLOAT):
            self.advance()
            return NumberNode(tok)

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    def expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    def bin_op(self, func, ops):
        left = func()

        while self.current_tok is not None and self.current_tok.type in ops:
            op_tok = self.current_tok
            self.advance()
            right = func()
            left = BinOpNode(left, op_tok, right)

        return left

###########################################
# RUN
###########################################

def run(fn, text):  # Run function to take in some text and run it
    # Generate Tokens
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    if error: 
        return None, error

    # Generate AST (Abstract Syntax Tree)
    parser = Parser(tokens)
    ast = parser.parse()

    return ast, None
