# 2252749
from MiniGoVisitor import MiniGoVisitor
from MiniGoParser import MiniGoParser
from AST import *
from functools import reduce

def flatten(lst):
    return reduce(lambda prev, curr: prev + curr, lst, [])

class ASTGeneration(MiniGoVisitor):
    
    
    # program: nullable_nl list_decl nullable_nl EOF;
    def visitProgram(self, ctx:MiniGoParser.ProgramContext):
        return Program(list(filter(None, self.visit(ctx.list_decl()))))


    
    # list_decl: declaration list_decl | declaration;
    def visitList_decl(self, ctx:MiniGoParser.List_declContext):
        if ctx.list_decl():
            return [self.visit(ctx.declaration())] + self.visit(ctx.list_decl())
        else:
            return [self.visit(ctx.declaration())]

    
    # declaration: type_declaration | var_decl sm_nl | funcdecl | const_decl sm_nl;
    def visitDeclaration(self, ctx:MiniGoParser.DeclarationContext):
        if ctx.const_decl():
            return self.visit(ctx.const_decl()) 
        elif ctx.var_decl():
            return self.visit(ctx.var_decl()) 
        elif ctx.funcdecl():
            return self.visit(ctx.funcdecl())
        else:
            return self.visit(ctx.type_declaration())



    
    # literal: INT_LIT 
    # | NIL 
    # | TRUE 
    # | FALSE 
    # | FLOAT_LIT 
    # | STRING_LIT 
    # ;
    # convert hex to int
    def visitLiteral(self, ctx:MiniGoParser.LiteralContext):
        if ctx.INT_LIT():
            return IntLiteral(ctx.INT_LIT().getText())
        elif ctx.NIL():
            return NilLiteral()
        elif ctx.TRUE():
            return BooleanLiteral(True)
        elif ctx.FALSE():
            return BooleanLiteral(False)
        elif ctx.FLOAT_LIT():
            return FloatLiteral(ctx.FLOAT_LIT().getText())
        else:
            return StringLiteral(ctx.STRING_LIT().getText())


    # array_literal: array_type LBRACE list_element RBRACE;
    def visitArray_literal(self, ctx: MiniGoParser.Array_literalContext):
        array_type = self.visit(ctx.array_type())
        elements = flatten(self.visit(ctx.list_element()))
        dimens = [IntLiteral(dim.value) if isinstance(dim, IntLiteral) else Id(dim.name) for dim in array_type.dimens]
        return ArrayLiteral(dimens, array_type.eleType, elements)

    # list_element: array_element CM list_element | array_element;
    def visitList_element(self, ctx:MiniGoParser.List_elementContext):
        if ctx.list_element():
            return [self.visit(ctx.array_element())] + self.visit(ctx.list_element())
        else:
            return [self.visit(ctx.array_element())]

    # array_element: one_element | multi_element;
    def visitArray_element(self, ctx:MiniGoParser.Array_elementContext):
        return self.visit(ctx.getChild(0))

    # one_element: type_var_arr CM one_element | type_var_arr;
    def visitOne_element(self, ctx:MiniGoParser.One_elementContext):
        if ctx.one_element():
            return [self.visit(ctx.type_var_arr())] + self.visit(ctx.one_element())
        else:
            return [self.visit(ctx.type_var_arr())]

    # multi_element: LBRACE array_element CM multi_element RBRACE | LBRACE array_element RBRACE;
    def visitMulti_element(self, ctx:MiniGoParser.Multi_elementContext):
        if ctx.multi_element():
            return [self.visit(ctx.array_element()) + self.visit(ctx.multi_element())]
        else:
            return [self.visit(ctx.array_element())]

    # type_var_arr: literal | ID | struct_literal;
    def visitType_var_arr(self, ctx:MiniGoParser.Type_var_arrContext):
        if ctx.literal():
            return self.visit(ctx.literal())
        elif ctx.ID():
            return Id(ctx.ID().getText())
        else:
            return self.visit(ctx.struct_literal())

    # struct_literal: ID LBRACE nullable_struct_element_list RBRACE;
    def visitStruct_literal(self, ctx:MiniGoParser.Struct_literalContext):
        elements = self.visit(ctx.nullable_struct_element_list())
        return StructLiteral(ctx.ID().getText(), elements if elements is not None else [])

    # nullable_struct_element_list: nn_struct_element | ;
    def visitNullable_struct_element_list(self, ctx:MiniGoParser.Nullable_struct_element_listContext):
        if ctx.nn_struct_element():
            return self.visit(ctx.nn_struct_element())
        else:
            return []


    
    # nn_struct_element: struct_element CM nn_struct_element | struct_element; 
    def visitNn_struct_element(self, ctx:MiniGoParser.Nn_struct_elementContext):
        if ctx.nn_struct_element():
            return [self.visit(ctx.struct_element())] + self.visit(ctx.nn_struct_element())  
        else:
            return [self.visit(ctx.struct_element())]


    # struct_element: ID COLON expr;
    def visitStruct_element(self, ctx:MiniGoParser.Struct_elementContext):
        return (ctx.ID().getText(), self.visit(ctx.expr()))
        

    
    # type_declaration: struct_type | interface_type; 
    def visitType_declaration(self, ctx:MiniGoParser.Type_declarationContext):
        if ctx.struct_type():
            return self.visit(ctx.struct_type())
        else:
            return self.visit(ctx.interface_type())


    # array_type: dimension_list var_type; 
    def visitArray_type(self, ctx:MiniGoParser.Array_typeContext):
        return ArrayType(self.visit(ctx.dimension_list()), self.visit(ctx.var_type()))


    # dimension_list: dimension dimension_list | dimension;
    def visitDimension_list(self, ctx:MiniGoParser.Dimension_listContext):
        if ctx.dimension_list():
            return [self.visit(ctx.dimension())] + self.visit(ctx.dimension_list())
        else:
            return [self.visit(ctx.dimension())]

    
    # dimension: LBRACKET INT_LIT RBRACKET | LBRACKET ID RBRACKET;
    def visitDimension(self, ctx:MiniGoParser.DimensionContext):
        if ctx.INT_LIT():
            return IntLiteral(int(ctx.INT_LIT().getText(), 0))
        else:
            return Id(ctx.ID().getText())



    
    # struct_type: TYPE ID STRUCT struct_fields sm_nl; 
    def visitStruct_type(self, ctx:MiniGoParser.Struct_typeContext):
        return StructType(ctx.ID().getText(), self.visit(ctx.struct_fields()), [])


    
    # struct_fields: LBRACE field_list RBRACE ; 
    def visitStruct_fields(self, ctx:MiniGoParser.Struct_fieldsContext):
        return self.visit(ctx.field_list())


    
    # field_list: field field_list | field; 
    def visitField_list(self, ctx:MiniGoParser.Field_listContext):
        if ctx.field_list():
            return [self.visit(ctx.field())] + self.visit(ctx.field_list())
        else:
            return [self.visit(ctx.field())]


    
    # field: ID var_type sm_nl; 
    def visitField(self, ctx:MiniGoParser.FieldContext):
        return (ctx.ID().getText(), self.visit(ctx.var_type()))


    
    # interface_type: TYPE ID INTERFACE method_block sm_nl;
    def visitInterface_type(self, ctx:MiniGoParser.Interface_typeContext):
        methods = self.visit(ctx.method_block())
        return InterfaceType(ctx.ID().getText(), methods if methods is not None else [])


    
    # method_block: LBRACE methods RBRACE;
    def visitMethod_block(self, ctx:MiniGoParser.Method_blockContext):
        return self.visit(ctx.methods()) if ctx.methods() else []


    
    # nullable_methods: methods | ;
    def visitNullable_methods(self, ctx:MiniGoParser.Nullable_methodsContext):
        if ctx.methods():
            return self.visit(ctx.methods())
        else:
            return []

    
    # methods: method1 methods | method1;
    def visitMethods(self, ctx:MiniGoParser.MethodsContext):
        if ctx.methods():
            return [self.visit(ctx.method1())] + self.visit(ctx.methods())
        else:
            return [self.visit(ctx.method1())]


    
    # method1: method sm_nl;
    def visitMethod1(self, ctx:MiniGoParser.Method1Context):
        return self.visit(ctx.method())


    # method: ID LPAREN nullable_param_list RPAREN optional_return_type;
    def visitMethod(self, ctx:MiniGoParser.MethodContext):
        id = ctx.ID().getText()
        param_list = [param.parType for param in self.visit(ctx.nullable_param_list())]
        return_type = self.visit(ctx.optional_return_type())
        return Prototype(id, param_list, return_type)

    
    # optional_return_type: var_type | ;
    def visitOptional_return_type(self, ctx:MiniGoParser.Optional_return_typeContext):
        if ctx.var_type():
            return self.visit(ctx.var_type())
        else:
            return VoidType()

    
    # nullable_param_list: paramprime | ;
    def visitNullable_param_list(self, ctx:MiniGoParser.Nullable_param_listContext):
        if ctx.paramprime():
            return self.visit(ctx.paramprime())
        else:
            return []


    
    # paramprime: param CM paramprime | param;
    def visitParamprime(self, ctx:MiniGoParser.ParamprimeContext):
        # return [self.visit(ctx.param())] + self.visit(ctx.paramprime()) if ctx.paramprime() else [self.visit(ctx.param())]
        return reduce(lambda x, y: x + y, [self.visit(ctx.param())] + [self.visit(ctx.paramprime())] if ctx.paramprime() else [self.visit(ctx.param())])


    # param: idlist var_type;
    def visitParam(self, ctx:MiniGoParser.ParamContext):
        idList = self.visit(ctx.idlist())
        varType = self.visit(ctx.var_type())
        return [ParamDecl(id, varType) for id in idList]

    # idlist: ID CM idlist | ID;
    def visitIdlist(self, ctx:MiniGoParser.IdlistContext):
        if ctx.getChildCount() == 1:
            return [ctx.ID().getText()]
        else:
            return [ctx.ID().getText()] + self.visit(ctx.idlist())



    # var_decl_list: var_decl var_decl_list | var_decl;
    def visitVar_decl_list(self, ctx:MiniGoParser.Var_decl_listContext):
        if ctx.var_decl_list():
            return [self.visit(ctx.var_decl())]+ self.visit(ctx.var_decl_list())
        else:
            return [self.visit(ctx.var_decl())]


    # var_decl: VAR ID var_decl_body;
    def visitVar_decl(self, ctx:MiniGoParser.Var_declContext):
        varName = ctx.ID().getText()
        varBody = self.visit(ctx.var_decl_body())
        if isinstance(varBody, list):
            varType, varInit = varBody
        else:
            varType, varInit = None, varBody
        return VarDecl(varName, varType, varInit)

    # var_decl_body: var_type | ASSIGN_INIT expr | var_type ASSIGN_INIT expr;
    def visitVar_decl_body(self, ctx:MiniGoParser.Var_decl_bodyContext):
        if ctx.getChildCount() == 1: return self.visit(ctx.var_type())
        elif ctx.getChildCount() == 2: return self.visit(ctx.expr())
        else: return [self.visit(ctx.var_type()), self.visit(ctx.expr())]

    
    # const_decl_list: const_decl const_decl_list | const_decl;
    def visitConst_decl_list(self, ctx:MiniGoParser.Const_decl_listContext):
        if ctx.const_decl_list():
            return [self.visit(ctx.const_decl())] + self.visit(ctx.const_decl_list())
        else:
            return [self.visit(ctx.const_decl())]


    # const_decl: CONST ID ASSIGN_INIT expr;
    def visitConst_decl(self, ctx:MiniGoParser.Const_declContext):
        return ConstDecl(ctx.ID().getText(), None, self.visit(ctx.expr()))


    
    # funcdecl: func_decl | method_decl;
    def visitFuncdecl(self, ctx:MiniGoParser.FuncdeclContext):
        if ctx.func_decl():
            return self.visit(ctx.func_decl())
        else:
            return self.visit(ctx.method_decl())


    # func_decl: FUNC ID LPAREN nullable_param_list RPAREN optional_return_type LBRACE block_list RBRACE sm_nl; 
    def visitFunc_decl(self, ctx:MiniGoParser.Func_declContext):
        return FuncDecl(ctx.ID().getText(), self.visit(ctx.nullable_param_list()), self.visit(ctx.optional_return_type()), Block(self.visit(ctx.block_list())))


    
    # block_list: block_code_prime | ;
    def visitBlock_list(self, ctx:MiniGoParser.Block_listContext):
        if ctx.block_code_prime():
            return self.visit(ctx.block_code_prime())
        else:
            return []


    
    # block_code_prime: stmt block_code_prime | stmt;
    def visitBlock_code_prime(self, ctx:MiniGoParser.Block_code_primeContext):
        if ctx.block_code_prime():
            return [self.visit(ctx.stmt())] + self.visit(ctx.block_code_prime())
        else:
            return [self.visit(ctx.stmt())]


    # method_decl: FUNC reciever ID LPAREN nullable_param_list RPAREN optional_return_type LBRACE block_list RBRACE sm_nl;
    def visitMethod_decl(self, ctx:MiniGoParser.Method_declContext):
        receiver = self.visit(ctx.reciever())
        id = ctx.ID().getText()
        param_list = self.visit(ctx.nullable_param_list())
        return_type = self.visit(ctx.optional_return_type())
        block = Block(self.visit(ctx.block_list()))
        return MethodDecl(receiver[0], receiver[1], FuncDecl(id, param_list, return_type, block))

    
    # reciever: LPAREN ID ID RPAREN;
    def visitReciever(self, ctx:MiniGoParser.RecieverContext):
        return [ctx.ID(0).getText(), Id(ctx.ID(1).getText())]


    
    # expr_list_prime: expr_list sm_nl; 
    def visitExpr_list_prime(self, ctx:MiniGoParser.Expr_list_primeContext):
        return self.visit(ctx.expr_list())


    
    # expr_list: expr CM expr_list | expr;
    def visitExpr_list(self, ctx:MiniGoParser.Expr_listContext):
        if ctx.expr_list():
            return [self.visit(ctx.expr())] + self.visit(ctx.expr_list())
        else:
            return [self.visit(ctx.expr())]


    # expr: expr OR expr1 | expr1;
    def visitExpr(self, ctx:MiniGoParser.ExprContext):
        if ctx.OR():
            return BinaryOp(ctx.OR().getText(), self.visit(ctx.expr()), self.visit(ctx.expr1()))
        else:
            return self.visit(ctx.expr1())


    # expr1: expr1 AND expr2 | expr2;
    def visitExpr1(self, ctx:MiniGoParser.Expr1Context):
        if ctx.AND():
            return BinaryOp(ctx.AND().getText(), self.visit(ctx.expr1()), self.visit(ctx.expr2()))
        else:
            return self.visit(ctx.expr2())


    
    # expr2: expr2 relational_ops expr3 | expr3;
    def visitExpr2(self, ctx:MiniGoParser.Expr2Context):
        if ctx.relational_ops():
            return BinaryOp(self.visit(ctx.relational_ops()), self.visit(ctx.expr2()), self.visit(ctx.expr3()))
        else:
            return self.visit(ctx.expr3())


    
    # expr3: expr3 ADD expr4 | expr3 SUB expr4 | expr4;
    def visitExpr3(self, ctx:MiniGoParser.Expr3Context):
        if ctx.ADD():
            return BinaryOp(ctx.ADD().getText(), self.visit(ctx.expr3()), self.visit(ctx.expr4()))
        elif ctx.SUB():
            return BinaryOp(ctx.SUB().getText(), self.visit(ctx.expr3()), self.visit(ctx.expr4()))
        else:
            return self.visit(ctx.expr4())


    
    # expr4: expr4 MUL expr5 | expr4 DIV expr5 | expr4 MOD expr5 | expr5;
    def visitExpr4(self, ctx:MiniGoParser.Expr4Context):
        if ctx.MUL():
            return BinaryOp(ctx.MUL().getText(), self.visit(ctx.expr4()), self.visit(ctx.expr5()))
        elif ctx.DIV():
            return BinaryOp(ctx.DIV().getText(), self.visit(ctx.expr4()), self.visit(ctx.expr5()))
        elif ctx.MOD():
            return BinaryOp(ctx.MOD().getText(), self.visit(ctx.expr4()), self.visit(ctx.expr5()))
        else:
            return self.visit(ctx.expr5())


    
    # expr5: NOT expr5 | SUB expr5 | expr6;
    def visitExpr5(self, ctx:MiniGoParser.Expr5Context):
        if ctx.NOT():
            return UnaryOp(ctx.NOT().getText(), self.visit(ctx.expr5()))
        elif ctx.SUB():
            return UnaryOp(ctx.SUB().getText(), self.visit(ctx.expr5()))
        else:
            return self.visit(ctx.expr6())


    # expr6: expr6 LBRACKET expr RBRACKET | expr6 DOT ID (LPAREN nullable_expr RPAREN)? | operand;
    def visitExpr6(self, ctx:MiniGoParser.Expr6Context):
        base = self.visit(ctx.expr6()) if ctx.expr6() else None

        if ctx.LPAREN(): 
            args = self.visit(ctx.nullable_expr()) or []
            if isinstance(base, MethCall) or isinstance(base, FuncCall):
                return MethCall(base, ctx.ID().getText(), args)
            return MethCall(base, ctx.ID().getText(), args)

        elif ctx.ID():  
            if isinstance(base, MethCall) or isinstance(base, FuncCall):
                return MethCall(base, Id(ctx.ID().getText()), [])
            
            return FieldAccess(base, ctx.ID().getText())

        elif ctx.expr():
            index = self.visit(ctx.expr())
            if isinstance(base, ArrayCell):
                return ArrayCell(base.arr, base.idx + [index])  
            else:
                return ArrayCell(base, [index])

        else:
            return self.visit(ctx.operand())    



    
    # operand: literal | LPAREN expr RPAREN | ID | func_call | struct_literal | array_literal;
    def visitOperand(self, ctx:MiniGoParser.OperandContext):
        if ctx.literal():
            return self.visit(ctx.literal())
        elif ctx.ID():
            return Id(ctx.ID().getText())
        elif ctx.func_call():
            return self.visit(ctx.func_call())
        elif ctx.struct_literal():
            return self.visit(ctx.struct_literal())
        elif ctx.array_literal():
            return self.visit(ctx.array_literal())
        else:
            return self.visit(ctx.expr())


    
    # relational_ops: STR_EQ | NOT_EQUAL | LT | LE | GT | GE;
    def visitRelational_ops(self, ctx:MiniGoParser.Relational_opsContext):
        if ctx.STR_EQ():
            return ctx.STR_EQ().getText()
        elif ctx.NOT_EQUAL():
            return ctx.NOT_EQUAL().getText()
        elif ctx.LT():
            return ctx.LT().getText()
        elif ctx.LE():
            return ctx.LE().getText()
        elif ctx.GT():
            return ctx.GT().getText()
        else:
            return ctx.GE().getText()


    # struct_access: DOT ID;
    def visitStruct_access(self, ctx:MiniGoParser.Struct_accessContext):
        return FieldAccess(Id(ctx.ID().getText()), Id(ctx.ID().getText()))


    #correct
    # stmt_list: stmt stmt_list | stmt;
    def visitStmt_list(self, ctx:MiniGoParser.Stmt_listContext):
        if ctx.stmt_list():
            return [self.visit(ctx.stmt())] + self.visit(ctx.stmt_list())
        else:
            return [self.visit(ctx.stmt())]


    
    # stmt: stmt_type sm_nl;
    def visitStmt(self, ctx:MiniGoParser.StmtContext):
        return self.visit(ctx.stmt_type())


    
    # stmt_type: const_decl | var_decl |assign_stmt | if_stmt | for_stmt | break_stmt | cont_stmt | call_stmt | return_stmt;
    def visitStmt_type(self, ctx:MiniGoParser.Stmt_typeContext):
        if ctx.const_decl():
            return self.visit(ctx.const_decl())
        elif ctx.var_decl():
            return self.visit(ctx.var_decl())
        elif ctx.assign_stmt():
            return self.visit(ctx.assign_stmt())
        elif ctx.if_stmt():
            return self.visit(ctx.if_stmt())
        elif ctx.for_stmt():
            return self.visit(ctx.for_stmt())
        elif ctx.break_stmt():
            return self.visit(ctx.break_stmt())
        elif ctx.cont_stmt():
            return self.visit(ctx.cont_stmt())
        elif ctx.call_stmt():
            return self.visit(ctx.call_stmt())
        else:
            return self.visit(ctx.return_stmt())


    # assign_stmt: assign_lhs assign_ops expr;
    def visitAssign_stmt(self, ctx:MiniGoParser.Assign_stmtContext):
        lhs = self.visit(ctx.assign_lhs())
        op = ctx.assign_ops().getText()
        rhs = self.visit(ctx.expr())
        if isinstance(lhs, str):
            lhs = Id(lhs)
        if op == ":=":
            return Assign(lhs, rhs)
        else:
            return Assign(lhs, BinaryOp(op[:-1], lhs, rhs))

    # assign_lhs: ID | assign_lhs LBRACKET expr RBRACKET | assign_lhs struct_access;
    def visitAssign_lhs(self, ctx:MiniGoParser.Assign_lhsContext):
        if ctx.getChildCount() == 1:
            return Id(ctx.ID().getText())
        elif ctx.LBRACKET():
            lhs = self.visit(ctx.assign_lhs())
            index = self.visit(ctx.expr())
            if isinstance(lhs, ArrayCell):
                return ArrayCell(lhs.arr, lhs.idx + [index])
            else:
                return ArrayCell(lhs, [index])
        else:
            lhs = self.visit(ctx.assign_lhs())
            field = ctx.struct_access().ID().getText()
            return FieldAccess(lhs, field)


    
    # assign_ops: ASSIGN_ASSIGNMENT | ADD_ASSIGN | SUB_ASSIGN | MUL_ASSIGN | DIV_ASSIGN | MOD_ASSIGN;
    def visitAssign_ops(self, ctx:MiniGoParser.Assign_opsContext):
        if ctx.ASSIGN_ASSIGNMENT():
            return ctx.ASSIGN_ASSIGNMENT().getText()
        elif ctx.ADD_ASSIGN():
            return ctx.ADD_ASSIGN().getText()
        elif ctx.SUB_ASSIGN():
            return ctx.SUB_ASSIGN().getText()
        elif ctx.MUL_ASSIGN():
            return ctx.MUL_ASSIGN().getText()
        elif ctx.DIV_ASSIGN():
            return ctx.DIV_ASSIGN().getText()
        else:
            return ctx.MOD_ASSIGN().getText()


    # if_stmt: IF condition_block LBRACE block_list RBRACE optional_else_if_stmt optional_else_stmt;
    def visitIf_stmt(self, ctx:MiniGoParser.If_stmtContext):
        cond = self.visit(ctx.condition_block())
        block = Block(self.visit(ctx.block_list()))
        else_ifs = self.visit(ctx.optional_else_if_stmt())
        else_stmt = self.visit(ctx.optional_else_stmt())
        
        if else_ifs:
            for else_if in reversed(else_ifs):
                else_stmt = If(else_if.expr, else_if.thenStmt, else_stmt)
        
        return If(cond, block, else_stmt)

    
    # optional_else_if_stmt: else_if_stmt_prime | ;
    def visitOptional_else_if_stmt(self, ctx:MiniGoParser.Optional_else_if_stmtContext):
        return self.visit(ctx.else_if_stmt_prime()) if ctx.getChildCount() == 1 else []


    # else_if_stmt_prime: else_if_stmt else_if_stmt_prime | else_if_stmt;
    def visitElse_if_stmt_prime(self, ctx:MiniGoParser.Else_if_stmt_primeContext):
        return [self.visit(ctx.else_if_stmt())] + self.visit(ctx.else_if_stmt_prime()) if ctx.getChildCount() > 1 else [self.visit(ctx.else_if_stmt())]


    
    # optional_else_stmt: else_stmt | ;
    def visitOptional_else_stmt(self, ctx:MiniGoParser.Optional_else_stmtContext):
        if ctx.else_stmt():
            return self.visit(ctx.else_stmt())
        else:
            return None


    # else_if_stmt: ELSE IF condition_block LBRACE block_list RBRACE;
    def visitElse_if_stmt(self, ctx:MiniGoParser.Else_if_stmtContext):
        condition = self.visit(ctx.condition_block())
        block = Block(self.visit(ctx.block_list()))
        return If(condition, block, None)

    # else_stmt: ELSE LBRACE block_list RBRACE;
    def visitElse_stmt(self, ctx:MiniGoParser.Else_stmtContext):
        block = Block(self.visit(ctx.block_list()))
        return block


    
    # for_stmt: for_normal_form  | for_loop_form  | for_array_form ; 
    def visitFor_stmt(self, ctx:MiniGoParser.For_stmtContext):
        if ctx.for_normal_form():
            return self.visit(ctx.for_normal_form())
        elif ctx.for_loop_form():
            return self.visit(ctx.for_loop_form())
        else:
            return self.visit(ctx.for_array_form())


    # for_normal_form: FOR expr LBRACE (stmt_list | ) RBRACE ;
    def visitFor_normal_form(self, ctx:MiniGoParser.For_normal_formContext):
        condition = self.visit(ctx.expr())
        if isinstance(condition, FieldAccess) or isinstance(condition, ArrayCell):
            condition = condition
        loop = Block(self.visit(ctx.stmt_list())) if ctx.stmt_list() else Block([])
        return ForBasic(condition, loop)
        

    # for_loop_form: FOR initial_expr sm_nl expr sm_nl ID assign_ops scalar_var LBRACE block_list RBRACE ;
    def visitFor_loop_form(self, ctx:MiniGoParser.For_loop_formContext):
        init = self.visit(ctx.initial_expr())
        condition = self.visit(ctx.expr())
        assignOp = ctx.assign_ops().getText()
        if assignOp == ":=":
            rhs = self.visit(ctx.scalar_var())
        else:
            rhs = BinaryOp(assignOp[:-1], Id(ctx.ID().getText()), self.visit(ctx.scalar_var()))
        update = Assign(Id(ctx.ID().getText()), rhs)
        loop = Block(self.visit(ctx.block_list()))
        return ForStep(init, condition, update, loop)
        

    # for_array_form: FOR ID CM scalar_var_vec ASSIGN_ASSIGNMENT RANGE expr LBRACE block_list RBRACE ;
    def visitFor_array_form(self, ctx:MiniGoParser.For_array_formContext):
        idx = Id(ctx.ID().getText())
        val = self.visit(ctx.scalar_var_sec())
        arr = self.visit(ctx.expr())
        loop = Block(self.visit(ctx.block_list()))
        return ForEach(idx, val, arr, loop)
        
    
    # scalar_var: ID | INT_LIT | FLOAT_LIT | STRING_LIT | TRUE | FALSE | expr;
    def visitScalar_var(self, ctx:MiniGoParser.Scalar_varContext):
        if ctx.ID():
            return Id(ctx.ID().getText())
        elif ctx.INT_LIT():
            return IntLiteral(ctx.INT_LIT().getText())
        elif ctx.FLOAT_LIT():
            return FloatLiteral(ctx.FLOAT_LIT().getText())
        elif ctx.STRING_LIT():
            return StringLiteral(ctx.STRING_LIT().getText())
        elif ctx.TRUE():
            return BooleanLiteral(True)
        elif ctx.FALSE():
            return BooleanLiteral(False)
        else:
            return self.visit(ctx.expr())
        
    # Visit a parse tree produced by MiniGoParser#scalar_var_sec.
    def visitScalar_var_sec(self, ctx:MiniGoParser.Scalar_var_secContext):
        if ctx.ID():
            return Id(ctx.ID().getText())
        elif ctx.INT_LIT():
            return IntLiteral(ctx.INT_LIT().getText())
        elif ctx.FLOAT_LIT():
            return FloatLiteral(ctx.FLOAT_LIT().getText())
        elif ctx.STRING_LIT():
            return StringLiteral(ctx.STRING_LIT().getText())
        elif ctx.TRUE():
            return BooleanLiteral(True)
        else:
            return BooleanLiteral(False)

    
    # initial_expr: ID assign_ops scalar_var | var_decl_for;
    def visitInitial_expr(self, ctx:MiniGoParser.Initial_exprContext):
        if ctx.ID():
            id = Id(ctx.ID().getText())
            assign_operation = self.visit(ctx.assign_ops())
            scalar_var = self.visit(ctx.scalar_var())
            if assign_operation == ":=":  
                return Assign(id, scalar_var)  
            else:  
                return Assign(id, BinaryOp(assign_operation[:-1], id, scalar_var))
        else:
            return self.visit(ctx.var_decl_for())
       

    
    # var_decl_for: VAR ID ASSIGN_INIT expr | VAR ID var_type ASSIGN_INIT expr;
    def visitVar_decl_for(self, ctx:MiniGoParser.Var_decl_forContext):
        id = ctx.ID().getText()
        type = self.visit(ctx.var_type()) if ctx.var_type() else None
        expr = self.visit(ctx.expr())
        return VarDecl(id, type, expr)


    
    # condition_block: LPAREN expr RPAREN; 
    def visitCondition_block(self, ctx:MiniGoParser.Condition_blockContext):
        return self.visit(ctx.expr())


    
    # break_stmt: BREAK;
    def visitBreak_stmt(self, ctx:MiniGoParser.Break_stmtContext):
        return Break()


    
    # cont_stmt: CONTINUE;
    def visitCont_stmt(self, ctx:MiniGoParser.Cont_stmtContext):
        return Continue()


    
    # call_stmt: func_call | method_call;
    def visitCall_stmt(self, ctx:MiniGoParser.Call_stmtContext):
        if ctx.func_call():
            return self.visit(ctx.func_call())
        else:
            return self.visit(ctx.method_call())


    # func_call: ID LPAREN nullable_expr RPAREN;
    def visitFunc_call(self, ctx:MiniGoParser.Func_callContext):
        funcName = ctx.ID().getText()
        args = self.visit(ctx.nullable_expr()) 
        return FuncCall(funcName, args if args else [])


    
    # nullable_expr: expr_list | ;
    def visitNullable_expr(self, ctx:MiniGoParser.Nullable_exprContext):
        return self.visit(ctx.expr_list()) if ctx.getChildCount() == 1 else None


    # method_call: assign_lhs DOT func_call;
    def visitMethod_call(self, ctx:MiniGoParser.Method_callContext):
        obj = self.visit(ctx.assign_lhs()) 
        method_name = ctx.func_call().ID().getText()  
        args = self.visit(ctx.func_call().nullable_expr()) 
        return MethCall(obj, method_name, args if args else [])
        

    
    # return_stmt: RETURN nullable_expr;
    def visitReturn_stmt(self, ctx:MiniGoParser.Return_stmtContext):
        expr = self.visit(ctx.nullable_expr())
    
        if isinstance(expr, list) and len(expr) == 1:
            expr = expr[0]

        return Return(expr)


    
    # nullable_nl: nn_nl | ;
    def visitNullable_nl(self, ctx:MiniGoParser.Nullable_nlContext):
        return ctx.visitChildren(ctx)


    
    # nn_nl: NEWLINE nn_nl | NEWLINE;
    def visitNn_nl(self, ctx:MiniGoParser.Nn_nlContext):
        return ctx.visitChildren(ctx)


    
    # sm_nl: SM nullable_nl | nn_nl;  
    def visitSm_nl(self, ctx:MiniGoParser.Sm_nlContext):
        return ctx.visitChildren(ctx)

    
    # var_type: primitive_type | composite_type | ID;
    def visitVar_type(self, ctx:MiniGoParser.Var_typeContext):
        if(ctx.primitive_type()):
            return self.visit(ctx.primitive_type())
        elif(ctx.composite_type()):
            return self.visit(ctx.composite_type())
        else:
            return Id(ctx.ID().getText())


    
    # primitive_type: INT | FLOAT | BOOLEAN | STRING;
    def visitPrimitive_type(self, ctx:MiniGoParser.Primitive_typeContext):
        if(ctx.INT()):
            return IntType()
        elif(ctx.FLOAT()):
            return FloatType()
        elif(ctx.BOOLEAN()):
            return BoolType()
        else:
            return StringType()


    
    # composite_type: array_type | struct_type | interface_type ;
    def visitComposite_type(self, ctx:MiniGoParser.Composite_typeContext):
        return self.visit(ctx.getChild(0))
