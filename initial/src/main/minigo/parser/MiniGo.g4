grammar MiniGo;

@lexer::header {
# 2252749
from lexererr import *
}

@lexer::members {
def emit(self):
    tk = self.type
    if tk == self.UNCLOSE_STRING:       
        result = super().emit();
        raise UncloseString(result.text);
    elif tk == self.ILLEGAL_ESCAPE:
        result = super().emit();
        raise IllegalEscape(result.text);
    elif tk == self.ERROR_CHAR:
        result = super().emit();
        raise ErrorToken(result.text);   
    else:
        return super().emit();

lastToken = None

def nextToken(self):
    token = super().nextToken()
    self.lastToken = token
    return token


def convert(self):
    rtyp = self.lastToken.type if self.lastToken is not None else -1
    allowed = [
            MiniGoLexer.ID, MiniGoLexer.INT_LIT, MiniGoLexer.FLOAT_LIT, MiniGoLexer.STRING_LIT, MiniGoLexer.HEX_LIT, MiniGoLexer.BINARY_LIT, MiniGoLexer.OCTAL_LIT, MiniGoLexer.TRUE, MiniGoLexer.FALSE, MiniGoLexer.RETURN, MiniGoLexer.CONTINUE, MiniGoLexer.BREAK,
            MiniGoLexer.RBRACE, MiniGoLexer.RBRACKET, MiniGoLexer.RPAREN, MiniGoLexer.NIL
    ]
    return rtyp in allowed
}

options{
	language = Python3;
}


// ! ============================== PARSER ============================== */

program: nullable_nl list_decl nullable_nl EOF;
list_decl: declaration list_decl | declaration;
declaration: type_declaration | var_decl sm_nl | funcdecl | const_decl sm_nl;


//---------------- LITERAL ----------------// DONE

literal: INT_LIT 
    | NIL 
    | TRUE 
    | FALSE 
    | FLOAT_LIT 
    | STRING_LIT 
    ;

// array literal 
array_literal: array_type LBRACE list_element RBRACE;
list_element: array_element CM list_element | array_element;
array_element: one_element | multi_element;
one_element: type_var_arr CM one_element | type_var_arr;
multi_element: LBRACE array_element RBRACE CM multi_element | LBRACE array_element RBRACE;
type_var_arr: literal | ID | struct_literal;


// struct instance 
struct_literal: ID LBRACE nullable_struct_element_list RBRACE;
nullable_struct_element_list: nn_struct_element | ;
nn_struct_element: struct_element CM nn_struct_element | struct_element; 
struct_element: ID COLON expr;


//---------------- TYPE DECLARATION ----------------// DONE

type_declaration: struct_type | interface_type;


//---------------- ARRAY TYPE ----------------// DONE

array_type: dimension_list var_type; 
dimension_list: dimension | multi_dimension;
dimension: LBRACKET INT_LIT RBRACKET | LBRACKET ID RBRACKET;
multi_dimension: dimension multi_dimension | dimension;


//------------------- STRUCT TYPE -------------------// DONE

struct_type: TYPE ID STRUCT struct_fields sm_nl;
struct_fields: LBRACE field_list RBRACE ; 
//nullable_field_list: field_list | ;
field_list: field field_list | field;
field: ID var_type sm_nl;


//------------------- INTERFACE TYPE -------------------// DONE

interface_type: TYPE ID INTERFACE method_block sm_nl;
method_block: LBRACE methods RBRACE;
nullable_methods: methods | ;
methods: method1 methods | method1;
method1: method sm_nl;
method: ID LPAREN nullable_param_list RPAREN optional_return_type;
optional_return_type: var_type | ;

// paramlist
nullable_param_list: paramprime | ;
paramprime: param CM paramprime | param;
param: idlist var_type;

// idlist 
idlist: ID CM idlist | ID;


//------------------- VARIABLE DECLARATION -------------------// DONE

// var_decl_list: var_decl var_decl_list | var_decl;
var_decl: VAR ID var_decl_body;
var_decl_body: var_type | ASSIGN_INIT expr | var_type ASSIGN_INIT expr;


//------------------- CONST DECLARATION -------------------// DONE

// const_decl_list: const_decl const_decl_list | const_decl;
const_decl: CONST ID ASSIGN_INIT expr; // because literal already in expr


//------------------- FUNCTION DECLARATION -------------------// DONE

funcdecl: func_decl | method_decl;
func_decl: FUNC ID LPAREN nullable_param_list RPAREN optional_return_type LBRACE block_list RBRACE sm_nl; 
block_list: block_code_prime | ;
block_code_prime: stmt block_code_prime | stmt;
//block_code: stmt | var_decl | const_decl;


//------------------- METHOD DECLARATION -------------------// DONE

method_decl: FUNC reciever ID LPAREN nullable_param_list RPAREN optional_return_type LBRACE block_list RBRACE sm_nl;
reciever: LPAREN ID ID RPAREN;


//------------------- EXPRESSION -------------------// DONE

expr_list_prime: expr_list sm_nl; 
expr_list: expr CM expr_list | expr;

expr: expr OR expr1 | expr1;
expr1: expr1 AND expr2 | expr2;
expr2: expr2 relational_ops expr3 | expr3;
expr3: expr3 ADD expr4 | expr3 SUB expr4 | expr4;
expr4: expr4 MUL expr5 | expr4 DIV expr5 | expr4 MOD expr5 | expr5;
expr5: NOT expr5 | SUB expr5 | expr6;
expr6: expr6 LBRACKET expr RBRACKET | expr6 DOT ID (LPAREN expr_list? RPAREN)? | operand;
operand: literal | LPAREN expr RPAREN | ID | func_call | struct_literal | array_literal;
relational_ops: STR_EQ | NOT_EQUAL | LT | LE | GT | GE;

// struct_access
struct_access: DOT ID;

//------------------- STATEMENT -------------------// NEARLY DONE

stmt_list: stmt stmt_list | stmt;
stmt: stmt_type sm_nl;
stmt_type: const_decl | var_decl |assign_stmt | if_stmt | for_stmt | break_stmt | cont_stmt | call_stmt | return_stmt;


// Assignment statement
assign_stmt: assign_lhs assign_ops expr;
assign_lhs: ID | assign_lhs LBRACKET expr RBRACKET | assign_lhs struct_access;
assign_ops: ASSIGN_ASSIGNMENT | ADD_ASSIGN | SUB_ASSIGN | MUL_ASSIGN | DIV_ASSIGN | MOD_ASSIGN;

// If statement
if_stmt: IF condition_block LBRACE block_list RBRACE optional_else_if_stmt optional_else_stmt;
optional_else_if_stmt: else_if_stmt_prime | ;
else_if_stmt_prime: else_if_stmt else_if_stmt_prime | else_if_stmt;
optional_else_stmt: else_stmt | ;
else_if_stmt: ELSE IF condition_block LBRACE block_list RBRACE;
else_stmt: ELSE LBRACE block_list RBRACE;

// For statement
for_stmt: for_normal_form  | for_loop_form  | for_array_form ; 
for_normal_form: FOR expr LBRACE (stmt_list | ) RBRACE ;
for_loop_form: FOR initial_expr sm_nl expr sm_nl ID assign_ops scalar_var LBRACE block_list RBRACE ;
for_array_form: FOR (INT_LIT | '_' | ID) CM scalar_var ASSIGN_ASSIGNMENT RANGE (ID | INT_LIT | ID dimension_list | struct_literal) LBRACE block_list RBRACE ;
scalar_var: ID | INT_LIT | FLOAT_LIT | STRING_LIT | TRUE | FALSE;

initial_expr: ID assign_ops scalar_var | var_decl_for;
var_decl_for: VAR ID ASSIGN_INIT expr | VAR ID var_type ASSIGN_INIT expr;
condition_block: LPAREN expr RPAREN; 

// Break statement
break_stmt: BREAK;

// Continue statement
cont_stmt: CONTINUE;

// Call statement
call_stmt: func_call | method_call;
func_call: assign_lhs LPAREN nullable_expr RPAREN;
nullable_expr: expr_list | ;
method_call: assign_lhs DOT func_call;

// Return statement
return_stmt: RETURN nullable_expr;


//------------------- SEMICOLON OR NEWLINE -------------------// 

nullable_nl: nn_nl | ;
nn_nl: NEWLINE nn_nl | NEWLINE;
sm_nl: SM nullable_nl | nn_nl;  


//------------------- TYPE OF VARIABLE -------------------//

var_type: primitive_type | composite_type | ID;
primitive_type: INT | FLOAT | BOOLEAN | STRING;
composite_type: array_type | struct_type | interface_type ;


//! ============================== PARSER ============================== */




// ! ============================== LEXER ============================== */

//TODO Keywords 3.3.2 pdf
IF: 'if';
ELSE: 'else';
FOR: 'for';
RETURN: 'return';
FUNC: 'func';
TYPE: 'type';
STRUCT: 'struct';
INTERFACE: 'interface';
STRING: 'string';
INT: 'int';
FLOAT: 'float';
BOOLEAN: 'boolean';
CONST: 'const';
VAR: 'var';
CONTINUE: 'continue';
BREAK: 'break';
RANGE: 'range';
NIL: 'nil';
TRUE: 'true';
FALSE: 'false';

//TODO Operators 3.3.3 pdf
ADD: '+';
SUB: '-';
MUL: '*';
DIV: '/';
MOD: '%';

STR_EQ: '==';
NOT_EQUAL: '!=';
LT: '<';
LE: '<=';
GT: '>';
GE: '>=';

AND: '&&';
OR: '||';
NOT: '!';

ASSIGN_INIT: '=';
ASSIGN_ASSIGNMENT: ':='; 
ADD_ASSIGN: '+=';
SUB_ASSIGN: '-=';
MUL_ASSIGN: '*=';
DIV_ASSIGN: '/=';
MOD_ASSIGN: '%=';

DOT: '.';


//TODO Separators 3.3.4 pdf
LPAREN: '(';
RPAREN: ')';
LBRACE: '{';
RBRACE: '}';
LBRACKET: '[';
RBRACKET: ']';
CM: ',';
SM: ';';
COLON: ':';

//TODO Identifiers 3.3.1 pdf
ID: [a-zA-Z_][a-zA-Z0-9_]*;

// Integer Literals
INT_LIT : DECIMAL_LIT | BINARY_LIT | OCTAL_LIT | HEX_LIT;
DECIMAL_LIT: '0' | [1-9][0-9]*;

BINARY_LIT
    : '0' [bB] Bin_digit+ 
    ;
OCTAL_LIT   
    : '0' [oO] Octal_digit+ 
    ;
HEX_LIT     
    : '0' [xX] Hex_digit+
    ;

fragment Octal_digit: [0-7];
fragment Hex_digit: [0-9a-fA-F];
fragment Bin_digit: [01];


//Floating-point Literals
FLOAT_LIT: [0-9]+ DOT [0-9]* Exponential?;
fragment Exponential: [eE] [+-]? [0-9]+;

//String Literals
STRING_LIT: '"' LEGAL_CHAR* '"';
fragment LEGAL_CHAR: ~["\r\n\\] | ESC_SEQ;
fragment ESC_SEQ: '\\' [ntr"\\];

//Boolean Literals
BOOLEAN_LIT: TRUE | FALSE;

//Nil Literals
NIL_LIT: NIL;

//TODO skip 3.1 and 3.2 pdf
NEWLINE: '\r'?'\n'
    {
        if self.convert():
            self.text = ';'
        else:
            self.skip()
    };

MULTI_LINE_COMMENT: '/*' (MULTI_LINE_COMMENT | .)*? '*/' -> skip;

SINGLE_LINE_COMMENT: '//' ~[\n\r]* ('\\' [rn])? -> skip;
WS: [ \t\f\r]+ -> skip;

//TODO ERROR pdf BTL1 + lexererr.py


UNCLOSE_STRING: '"' LEGAL_CHAR* ('\r\n' | '\n' | EOF) 
    {
        if len(self.text) >= 2 and self.text[-1] == '\n' and self.text[-2] == '\r':
            raise UncloseString(f'\"{self.text[1:-2]}') 
        elif self.text[-1] == '\n':
            raise UncloseString(f'\"{self.text[1:-1]}')  
        else:
            raise UncloseString(f'\"{self.text[1:]}') 
    }
    ;

ILLEGAL_ESCAPE: '"' LEGAL_CHAR* ('\r' | '\n' | '\\' ~[ntr"\\])
    {
        raise IllegalEscape(f'\"{self.text[1:]}')
    }
    ;

ERROR_CHAR: . {raise ErrorToken(self.text)};

//! ============================== LEXER ============================== */