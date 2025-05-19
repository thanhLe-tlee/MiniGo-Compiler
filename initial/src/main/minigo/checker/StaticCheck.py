"""
 * @author nhphung
 
ID: 2252749
"""
from AST import * 
from Visitor import *
from Utils import Utils
from StaticError import *
from functools import reduce
from typing import List, Tuple
from StaticError import Type as ErrorType
from AST import Type

class MType:
    def __init__(self,partype,rettype):
        self.partype = partype
        self.rettype = rettype

    def __str__(self):
        return "MType([" + ",".join(str(x) for x in self.partype) + "]," + str(self.rettype) + ")"


class Symbol:
    def __init__(self,name,mtype,value = None):
        self.name = name
        self.mtype = mtype
        self.value = value

    def __str__(self):
        return "Symbol(" + str(self.name) + "," + str(self.mtype) + ("" if self.value is None else "," + str(self.value)) + ")"

class StaticChecker(BaseVisitor,Utils):
        
    
    def __init__(self,ast):
        self.ast = ast
        self.list_type: List[Union[StructType, InterfaceType]] = []
        self.list_function: List[FuncDecl] =  [
                FuncDecl("getInt", [], IntType(), Block([])),
                FuncDecl("putInt", [ParamDecl("i", IntType())], VoidType(), Block([])),
                FuncDecl("putIntLn", [ParamDecl("i", IntType())], VoidType(), Block([])),
                FuncDecl("getFloat", [], FloatType(), Block([])),
                FuncDecl("putFloat", [ParamDecl("f", FloatType())], VoidType(), Block([])),
                FuncDecl("putFloatLn", [ParamDecl("f", FloatType())], VoidType(), Block([])),
                FuncDecl("getBool", [], BoolType(), Block([])),
                FuncDecl("putBool", [ParamDecl("b", BoolType())], VoidType(), Block([])),
                FuncDecl("putBoolLn", [ParamDecl("b", BoolType())], VoidType(), Block([])),
                FuncDecl("getString", [], StringType(), Block([])),
                FuncDecl("putString", [ParamDecl("s", StringType())], VoidType(), Block([])),
                FuncDecl("putStringLn", [ParamDecl("s", StringType())], VoidType(), Block([])),
                FuncDecl("putLn", [], VoidType(), Block([]))
            ]
        self.function_current: FuncDecl = None

    def check(self):
        self.visit(self.ast, None)
        
    # ----------------------------- HELPER FUNCTION --------------------------- #
    
    def isSameType(self, lhs: Type, rhs: Type) -> bool:
        
        if type(lhs) != type(rhs):
            return False
        if isinstance(lhs, ArrayType) and isinstance(rhs, ArrayType):
            if len(lhs.dimens) != len(rhs.dimens):
                return False
            for ldim, rdim in zip(lhs.dimens, rhs.dimens):
                if isinstance(ldim, IntLiteral) and isinstance(rdim, IntLiteral):
                    if ldim.value != rdim.value:
                        return False
            return self.isSameType(lhs.eleType, rhs.eleType)
        return True
    
    def strictEqual(self, lhs: Type, rhs: Type) -> bool:
        if type(lhs) != type(rhs):
            return False
        if isinstance(lhs, ArrayType) and isinstance(rhs, ArrayType):
            if len(lhs.dimens) != len(rhs.dimens):
                return False
            for ldim, rdim in zip(lhs.dimens, rhs.dimens):
                if isinstance(ldim, IntLiteral) and isinstance(rdim, IntLiteral):
                    if ldim.value != rdim.value:
                        return False
            return self.strictEqual(lhs.eleType, rhs.eleType)
        if isinstance(lhs, Id) and isinstance(rhs, Id):
            return lhs.name == rhs.name
        return True



    
    def evalConstExpr(self, expr: Expr, c: List[List[Symbol]]) -> Union[int, None]:
        if isinstance(expr, IntLiteral):
            return expr.value
        elif isinstance(expr, Id):
            symbol = self.lookup(expr.name, sum(c, []), lambda x: x.name)
            if symbol and isinstance(symbol.value, Expr):
                return self.evalConstExpr(symbol.value, c)
        elif isinstance(expr, BinaryOp):
            l = self.evalConstExpr(expr.left, c)
            r = self.evalConstExpr(expr.right, c)
            if l is not None and r is not None:
                if expr.op == '+': return l + r
                if expr.op == '-': return l - r
                if expr.op == '*': return l * r
                if expr.op == '/': return l // r 
        return None

    
    def checkSameType_1(self, LHS_type: Type, RHS_type: Type, list_type_permission: List[Tuple[Type, Type]] = []) -> bool:
        if type(RHS_type) == StructType and RHS_type.name == "":
            if type(LHS_type) in [Id,None,StructType,InterfaceType]:
                return True

        LHS_type = self.lookup(LHS_type.name, self.list_type, lambda x: x.name) if isinstance(LHS_type, Id) else LHS_type
        RHS_type = self.lookup(RHS_type.name, self.list_type, lambda x: x.name) if isinstance(RHS_type, Id) else RHS_type
        
        if isinstance(RHS_type, NilLiteral):
            return isinstance(LHS_type, InterfaceType)

        if (type(LHS_type), type(RHS_type)) in list_type_permission:
            if isinstance(LHS_type, InterfaceType) and isinstance(RHS_type, StructType):
                for method in LHS_type.methods:
                    if (
                        method.name not in [m.fun.name for m in RHS_type.methods] or 
                        type(method.retType) not in [type(m.fun.retType) for m in RHS_type.methods] or 
                        (isinstance(method.retType, Id) and method.retType.name not in [
                            m.fun.retType.name for m in RHS_type.methods if isinstance(m.fun.retType, Id)
                        ])
                    ):
                        return False
                    matched = False
                    for meth in RHS_type.methods:
                        if meth.fun.name == method.name and len(method.params) == len(meth.fun.params):
                            param_match = all(
                                self.checkSameType_1(ltype, rtype.parType)
                                for ltype, rtype in zip(method.params, meth.fun.params)
                            )
                            return_match = self.checkSameType_1(method.retType, meth.fun.retType)

                            if param_match and return_match:
                                matched = True
                                break
                    if not matched:
                        return False

                return True
            return True

        if isinstance(LHS_type, (StructType, InterfaceType)) and isinstance(RHS_type, (StructType, InterfaceType)):
            return LHS_type.name == RHS_type.name

        if isinstance(LHS_type, ArrayType) and isinstance(RHS_type, ArrayType):
            if isinstance(LHS_type.eleType, Id) and isinstance(RHS_type.eleType, Id):
                return LHS_type.eleType.name == RHS_type.eleType.name
            elif isinstance(LHS_type.eleType,(IntType, FloatType)) and isinstance(RHS_type.eleType,(IntType,FloatType)):
                if len(LHS_type.dimens) != len(RHS_type.dimens):
                    return False
                for lhs_dimen,rhs_dimen in zip(LHS_type.dimens,RHS_type.dimens):
                    if isinstance(lhs_dimen, IntLiteral) and isinstance(rhs_dimen, IntLiteral):
                        if lhs_dimen.value != rhs_dimen.value:
                            return False
                return True
            return type(LHS_type.eleType) == type(RHS_type.eleType)
        
        
        return type(LHS_type) == type(RHS_type)

    # ----------------------------- END HELPER FUNCTION --------------------------- #
    
    
    # ----------------------------- OPERATION --------------------------- #
    
    def visitBinaryOp(self, ast, c):
        LHS_type = self.visit(ast.left, c)
        RHS_type = self.visit(ast.right, c)

        if ast.op in ['+']:
            if self.checkSameType_1(LHS_type, RHS_type, [(IntType, FloatType), (FloatType, IntType)]):
                if type(LHS_type) == StringType:
                    return StringType()
                elif type(LHS_type) == FloatType:
                    return FloatType()
                elif type(RHS_type) == FloatType:
                    return FloatType()
                elif type(LHS_type) == IntType:
                    return IntType()
                elif type(RHS_type) == IntType:
                    return IntType()
                elif type (LHS_type) == IntType and type(RHS_type) == FloatType:
                    return FloatType()
                elif type (LHS_type) == FloatType and type(RHS_type) == IntType:
                    return FloatType()
                
        if type(LHS_type) != type(RHS_type):
            if isinstance(LHS_type, IntType) and isinstance(RHS_type, FloatType) and ast.op in [ '-', '*', '/']:
                return FloatType()
            elif isinstance(LHS_type, FloatType) and isinstance(RHS_type, IntType) and ast.op in [ '-', '*', '/']:
                return FloatType()
        if type(LHS_type) == type(RHS_type):
            if isinstance(LHS_type, IntType) and ast.op in ['-', '*', '/', '%']:
                return IntType()
            elif isinstance(LHS_type, FloatType) and ast.op in ['-', '*', '/']:
                return FloatType()
            elif isinstance(LHS_type, BoolType) and ast.op in ['&&', '||']:
                return BoolType()
            elif isinstance(LHS_type, StringType) and ast.op in ['==', '!=', '<', '<=', '>', '>=']:
                return BoolType()
            elif isinstance(LHS_type, (IntType, FloatType)) and ast.op in ['==', '!=', '<', '<=', '>', '>=']:
                return BoolType()
            elif isinstance(LHS_type, IntType) and isinstance(RHS_type, FloatType) and ast.op in [ '-', '*', '/']:
                return FloatType()
            elif isinstance(LHS_type, FloatType) and isinstance(RHS_type, IntType) and ast.op in [ '-', '*', '/']:
                return FloatType()
        raise TypeMismatch(ast)

    def visitUnaryOp(self, ast, c):
        unary_type = self.visit(ast.body, c)
        if ast.op == '-' and isinstance(unary_type, (IntType, FloatType)):
            return unary_type
        if ast.op == '!' and isinstance(unary_type, BoolType):
            return BoolType()
        raise TypeMismatch(ast)
    
    # ----------------------------- END OPERATION --------------------------- #

    def visitProgram(self, ast, c):
        declared_list = []
        def visitMethodDecl(ast, c):
            if ast.fun.name in [field[0] for field in c.elements]:
                raise Redeclared(Method(), ast.fun.name)
            method_struct = self.lookup(ast.fun.name, c.methods, lambda x: x.fun.name)
            if method_struct is not None:
                raise Redeclared(Method(), ast.fun.name)   
            c.methods.append(ast)  

        self.list_type = reduce(lambda acc, ele: [self.visit(ele, acc)] + acc if isinstance(ele, Type) else acc, ast.decl, [])
        
        for decl in ast.decl:
            if isinstance(decl, ConstDecl):
                if decl.conName in declared_list:
                    raise Redeclared(Constant(), decl.conName)  
                declared_list.append(decl.conName)
            elif isinstance(decl, Type):
                if decl.name in declared_list:
                    raise Redeclared(ErrorType(), decl.name)  
                declared_list.append(decl.name)
            elif isinstance(decl, VarDecl):
                if decl.varName in declared_list:
                    raise Redeclared(Variable(), decl.varName)  
                declared_list.append(decl.varName)
                
        # print("before: ",[f.name for f in self.list_function])
        self.list_function = self.list_function + list(filter(lambda item: isinstance(item, FuncDecl), ast.decl))
        # print ("after: ",[f.name for f in self.list_function])
        
        list(map(
            lambda item: visitMethodDecl(item, self.lookup(item.recType.name, self.list_type, lambda x: x.name)), 
             list(filter(lambda item: isinstance(item, MethodDecl), ast.decl))
        ))

        reduce(
            lambda acc, ele: [
                ([result] + acc[0]) if isinstance(result := self.visit(ele, acc), Symbol) else acc[0]
            ] + acc[1:], 
            filter(lambda item: isinstance(item, Decl), ast.decl), 
            [[
                Symbol("getInt",MType([],IntType())),
                Symbol("putIntLn",MType([IntType()],VoidType())),
                Symbol("putInt",MType([IntType()],VoidType())),
                Symbol("getFloat",MType([],FloatType())),
                Symbol("putFloatLn",MType([FloatType()],VoidType())),
                Symbol("putFloat",MType([FloatType()],VoidType())),
                Symbol("getBool",MType([],BoolType())),
                Symbol("putBool",MType([BoolType()],VoidType())),
                Symbol("putBoolLn",MType([BoolType()],VoidType())),
                Symbol("getString",MType([],StringType())),
                Symbol("putString",MType([StringType()],VoidType())),
                Symbol("putStringLn",MType([StringType()],VoidType())),
                Symbol("putLn",MType([],VoidType()))
            ]]
            
        
        ) 

    # ----------------------------- TYPE --------------------------- #

    def visitPrototype(self, ast, c):
        res = self.lookup(ast.name, c, lambda x: x.name)
        if res is not None:
            raise Redeclared(Prototype(), ast.name)
        
        res = self.lookup(ast.name, self.list_type, lambda x: x.name)
        if res is not None:
            raise Redeclared(Prototype(), ast.name)
        return ast

    def visitInterfaceType(self, ast, c):
        res = self.lookup(ast.name, c, lambda x: x.name)
        if not res is None:
            raise Redeclared(ErrorType(), ast.name)  
        builtin_conflict = self.lookup(ast.name, self.list_function, lambda x: x.name)
        if builtin_conflict is not None:
            raise Redeclared(ErrorType(), ast.name)
        ast.methods = reduce(lambda acc,ele: [self.visit(ele,acc)] + acc , ast.methods , [])
        return ast
    
    # ----------------------------- END TYPE --------------------------- #
    
    
    # ----------------------------- DECLARATION --------------------------- #
    
    def visitFuncDecl(self, ast, c):
        res = self.lookup(ast.name, c[0], lambda x: x.name)

        if res is not None:
            raise Redeclared(Function(), ast.name)
        self.function_current = ast   
        self.visit(ast.body, [list(reduce(lambda acc,ele: [self.visit(ele,acc)] + acc, ast.params, []))] + c)

        return Symbol(ast.name, MType([param.parType for param in ast.params], ast.retType), ast.body)

    def visitParamDecl(self, ast, c):
        res = self.lookup(ast.parName, c, lambda x: x.name)
        if res is not None:
            raise Redeclared(Parameter(), ast.parName)
        
        return Symbol(ast.parName, ast.parType, None)

    def visitMethodDecl(self, ast, c):
        struct_type = self.lookup(ast.recType.name, self.list_type, lambda x: x.name)
        param_scope = []
        for param in ast.fun.params:
            symbol = self.visitParamDecl(param, param_scope)
            param_scope.append(symbol)

        scope = param_scope + [Symbol(ast.receiver, struct_type)] 
        old_func = self.function_current
        self.function_current = ast.fun
        self.visit(ast.fun.body, [scope] + c)
        self.function_current = old_func
        
    def visitVarDecl(self, ast, c):
        res = self.lookup(ast.varName, self.list_type, lambda x: x.name)
        if res is not None:
            raise Redeclared(ErrorType(), ast.varName)
        res = self.lookup(ast.varName, c[0], lambda x: x.name)
        if not res is None:
            raise Redeclared(Variable(), ast.varName) 
        
        LHS_type = ast.varType if ast.varType else None
        RHS_type = self.visit(ast.varInit, c) if ast.varInit else None
        
        
        if RHS_type is None:
            return Symbol(ast.varName, LHS_type, None)
        elif LHS_type is None:
            return Symbol(ast.varName, RHS_type, None)
        elif isinstance(LHS_type, FloatType) and isinstance(RHS_type, IntType):
            return Symbol(ast.varName, LHS_type, None)
        elif self.checkSameType_1(LHS_type, RHS_type, [(FloatType, IntType), (InterfaceType, StructType)]):
            return Symbol(ast.varName, LHS_type, None)
        raise TypeMismatch(ast)
        

    def visitConstDecl(self, ast, c):
        res = self.lookup(ast.conName, self.list_type, lambda x: x.name)
        if res is not None:
            raise Redeclared(Constant(), ast.conName)
        res = self.lookup(ast.conName, c[0], lambda x: x.name)
        if res is not None:
            raise Redeclared(Constant(), ast.conName)
        
        
        rhs_type = self.visit(ast.iniExpr, c)
        symbol = Symbol(ast.conName, rhs_type, ast.iniExpr)
        return symbol

    # ----------------------------- END DECLARATION --------------------------- #
    

    # ----------------------------- STATEMENT --------------------------- #
    
    def visitForBasic(self, ast, c ): 
        cond_type = self.visit(ast.cond, c)
        if not isinstance(cond_type, BoolType):
            raise TypeMismatch(ast)
        self.visit(ast.loop, c)

    def visitForStep(self, ast, c): 
        acc = [[]] + c
        symbol = self.visit(ast.init, [[]] +  c)
        if isinstance(symbol, Symbol):
            acc[0] = [symbol] + acc[0]
        cond_type = self.visit(ast.cond, acc)
        if not isinstance(cond_type, BoolType):
            raise TypeMismatch(ast)
        self.visit(Block([ast.init, ast.upda] + ast.loop.member), acc)

    
    def visitForEach(self, ast, c): 
        acc = [[]] + c

        arr_type = self.visit(ast.arr, acc)
        if not isinstance(arr_type, ArrayType):
            raise TypeMismatch(ast.arr)

        key_symbol = self.lookup(ast.idx.name, sum(acc, []), lambda x: x.name)
        val_symbol = self.lookup(ast.value.name, sum(acc, []), lambda x: x.name)

        if key_symbol is None:
            raise Undeclared(Identifier(), ast.idx.name)
        if val_symbol is None:
            raise Undeclared(Identifier(), ast.value.name)
        
        if not isinstance(key_symbol.mtype, IntType):
            raise TypeMismatch(ast)
        
        if len(arr_type.dimens) <= 0:
            raise TypeMismatch(ast.arr)

        expected_val_type = (
            arr_type.eleType if len(arr_type.dimens) == 1
            else ArrayType(arr_type.dimens[1:], arr_type.eleType)
        )

        if not self.isSameType(val_symbol.mtype, expected_val_type):
            raise TypeMismatch(ast)
        
        if not self.strictEqual(val_symbol.mtype, expected_val_type):
            raise TypeMismatch(ast) 

         

        self.visit(ast.loop, acc)
        
    
    def visitFuncCall(self, ast, c):
        is_stmt = False
        if isinstance(c, tuple):
            c, is_stmt = c
        
        shadow = self.lookup(ast.funName, sum(c, []), lambda x: x.name)
        if shadow and not isinstance(shadow.mtype, MType):
            raise Undeclared(Function(), ast.funName)
        res = self.lookup(ast.funName, self.list_function, lambda x: x.name)
        if res:
            if len(res.params) != len(ast.args):
                raise TypeMismatch(ast)
            for param, arg in zip(res.params, ast.args):
                arg_type = self.visit(arg, c)
                if not self.checkSameType_1(param.parType, arg_type):
                    raise TypeMismatch(ast)
                if isinstance(param.parType, ArrayType) and isinstance(arg_type, ArrayType):
                    if type(param.parType.eleType) != type(arg_type.eleType):
                        raise TypeMismatch(ast)

                
            if is_stmt and not isinstance(res.retType, VoidType):
                raise TypeMismatch(ast)
            if not is_stmt and isinstance(res.retType, VoidType):
                raise TypeMismatch(ast)
            return res.retType
        raise Undeclared(Function(), ast.funName)

    def visitMethCall(self, ast, c):
        is_stmt = False
        if isinstance(c, tuple):
            c, is_stmt = c
        receiver_type = self.visit(ast.receiver, c)
        if isinstance(receiver_type, Id):
            receiver_type = self.lookup(receiver_type.name, self.list_type, lambda x: x.name)
        if not isinstance(receiver_type, (StructType, InterfaceType)):
            raise TypeMismatch(ast)
        
        if isinstance(receiver_type, StructType):
            res = self.lookup(ast.metName, receiver_type.methods, lambda x: x.fun.name)
            if res is None:
                raise Undeclared(Method(), ast.metName)
            
            if len(res.fun.params) != len(ast.args):
                raise TypeMismatch(ast)
            for param, arg in zip(res.fun.params, ast.args):
                arg_type = self.visit(arg, c)
                if not self.checkSameType_1(param.parType, arg_type, [(FloatType, IntType), (InterfaceType, StructType)]):
                    raise TypeMismatch(ast)
            if is_stmt and not isinstance(res.fun.retType, VoidType):
                raise TypeMismatch(ast)
            if not is_stmt and isinstance(res.fun.retType, VoidType):
                raise TypeMismatch(ast)
            return res.fun.retType
        elif isinstance(receiver_type, InterfaceType):
            res = self.lookup(ast.metName, receiver_type.methods, lambda x: x.name)
            if res is None:
                raise Undeclared(Method(), ast.metName)
            if res:
                if type(receiver_type) == StructType:
                    if len(res.fun.params) != len(ast.args):
                        raise TypeMismatch(ast)
                    for param, arg in zip(res.fun.params, ast.args):
                        arg_type = self.visit(arg, c)
                        if not self.checkSameType_1(param.parType, arg_type, [(FloatType, IntType), (InterfaceType, StructType)]):
                            raise TypeMismatch(ast)
                    if is_stmt and not isinstance(res.fun.retType, VoidType):
                        raise TypeMismatch(ast)
                    if not is_stmt and isinstance(res.fun.retType, VoidType):
                        raise TypeMismatch(ast)   
                    return res.fun.retType
                
                if type(receiver_type) == InterfaceType:
                    if len(res.params) != len(ast.args):
                        raise TypeMismatch(ast)
                    for param, arg in zip(res.params, ast.args):
                        arg_type = self.visit(arg, c)
                        if not self.checkSameType_1(param, arg_type, [(FloatType, IntType), (InterfaceType, StructType)]):
                            raise TypeMismatch(ast)
                    
                    if is_stmt and not isinstance(res.retType, VoidType):
                        raise TypeMismatch(ast)
                    if not is_stmt and isinstance(res.retType, VoidType):
                        raise TypeMismatch(ast)   
                    return res.retType
            raise Undeclared(Method(), ast.metName)

        
    def visitAssign(self, ast, c):
        try:
            lhs_type = self.visit(ast.lhs, c)
        except Undeclared as e:
            if isinstance(ast.lhs, Id):
                rhs_type = self.visit(ast.rhs, c)
                if self.lookup(ast.lhs.name, c[0], lambda x: x.name):
                    raise Redeclared(Variable(), ast.lhs.name)
                symbol = Symbol(ast.lhs.name, rhs_type)
                c[0].insert(0, symbol)
                return
            raise

        rhs_type = self.visit(ast.rhs, c)
        if not self.checkSameType_1(lhs_type, rhs_type, [(FloatType, IntType), (InterfaceType, StructType)]):
            raise TypeMismatch(ast)
        
    def visitIf(self, ast, c):
        cond_type = self.visit(ast.expr, c)
        if not isinstance(cond_type, BoolType):
            raise TypeMismatch(ast)
        self.visit(ast.thenStmt, c)
        if ast.elseStmt:
            self.visit(ast.elseStmt, c)

    def visitContinue(self, ast, c): return None
    def visitBreak(self, ast, c): return None
    def visitReturn(self, ast, c): 
        expr_type = self.visit(ast.expr, c) if ast.expr else VoidType()
    
        if isinstance(expr_type, Id):
            resolved = self.lookup(expr_type.name, self.list_type, lambda x: x.name)
            if resolved:
                expr_type = resolved
        
        expected_type = self.function_current.retType
        if isinstance(expected_type, Id):
            resolved = self.lookup(expected_type.name, self.list_type, lambda x: x.name)
            if resolved:
                expected_type = resolved

        if isinstance(expr_type, ArrayType) and isinstance(expected_type, ArrayType):
            if not isinstance(expr_type.eleType, type(expected_type.eleType)):
                raise TypeMismatch(ast)
            if len(expr_type.dimens) != len(expected_type.dimens):
                raise TypeMismatch(ast)
            for d1, d2 in zip(expr_type.dimens, expected_type.dimens):
                if isinstance(d1, IntLiteral) and isinstance(d2, IntLiteral):
                    if d1.value != d2.value:
                        raise TypeMismatch(ast)
        elif type(expr_type) != type(expected_type):
            raise TypeMismatch(ast)


    
    # ------------------------------- END STATEMENT --------------------------- #
    
    
    # ----------------------------- LITERAL --------------------------- #
    
    def visitIntLiteral(self, ast, c): return IntType()
    def visitFloatLiteral(self, ast, c): return FloatType()
    def visitBooleanLiteral(self, ast, c): return BoolType()
    def visitStringLiteral(self, ast, c): return StringType()
    def visitNilLiteral(self, ast, c): return StructType("", [], [])
    
    # ----------------------------- END LITERAL --------------------------- #
    
    
    # ----------------------------- ARRAY --------------------------- #
    
    def visitArrayType(self, ast, c):
        # list(map(lambda item: self.visit(item, c), ast.dimens))
        # return ast
        
        for dim in ast.dimens:
            value = self.evalConstExpr(dim, c)
            if value is None:
                raise TypeMismatch(ast)
        
        self.visit(ast.eleType, c)
        
        return ast
    
    def visitArrayCell(self, ast, c):
        array_type = self.visit(ast.arr, c)
        if not isinstance(array_type, ArrayType):
            raise TypeMismatch(ast)
       
        if not all(map(lambda item: self.checkSameType_1(self.visit(item, c), IntType()), ast.idx)):
            raise TypeMismatch(ast)
        if len(array_type.dimens) == len(ast.idx):
            return array_type.eleType
        elif len(array_type.dimens) > len(ast.idx):
            return ArrayType(array_type.dimens[len(ast.idx):], array_type.eleType)
        raise TypeMismatch(ast)

    def visitArrayLiteral(self, ast , c):  
        def nest2str(dat: Union[Literal, list['NestedList']], c: List[List[Symbol]]):
            if isinstance(dat,list):
                list(map(lambda value: nest2str(value, c), dat))
            else:
                self.visit(dat, c)
        nest2str(ast.value, c)
        return ArrayType(ast.dimens, ast.eleType)
    
    # ----------------------------- END ARRAY --------------------------- #
    
    
    # ----------------------------- STRUCT --------------------------- #
    
    def visitStructType(self, ast, c):
        declared_fields = {field[0] for field in ast.elements}
        for method in ast.methods:
            if method.fun.name in declared_fields:
                raise Redeclared(Method(), method.fun.name) 
            declared_fields.add(method.fun.name)
            
        res = self.lookup(ast.name, c, lambda x: x.name)
        if res is not None: 
            raise Redeclared(ErrorType(), ast.name)
        
        res = self.lookup(ast.name, self.list_function, lambda x: x.name)
        if res is not None:
            raise Redeclared(ErrorType(), ast.name)

        
        def visitElements(element, c):
            existed_element = self.lookup(element[0], c, lambda x: x[0])
            if existed_element is not None:
                raise Redeclared(Field(), element[0])
            
            struct_methods = ast.methods if hasattr(ast, 'methods') else []
            method_conflict = self.lookup(element[0], struct_methods, lambda x: x.fun.name)
            if method_conflict:
                raise Redeclared(Method(), element[0])
       
            return element

        ast.elements = reduce(lambda acc,ele: [visitElements(ele,acc)] + acc , ast.elements , [])
        return ast
    
    def visitStructLiteral(self, ast, c): 
        list(map(lambda value: self.visit(value[1], c), ast.elements))
        resolved = self.lookup(ast.name, self.list_type, lambda x: x.name)
        if resolved:
            return resolved
        raise Undeclared(ErrorType(), ast.name)
    
    def visitFieldAccess(self, ast, c):
        receiver_type = self.visit(ast.receiver, c)
        if isinstance(receiver_type, Id):
            receiver_type = self.lookup(receiver_type.name, self.list_type, lambda x: x.name)
            
        if not isinstance(receiver_type, StructType):
            raise TypeMismatch(ast)
        
        res = self.lookup(ast.field, receiver_type.elements, lambda x: x[0])
        if res is None:
            raise Undeclared(Field(), ast.field)
        return res[1]
    
    # ----------------------------- END STRUCT --------------------------- #
    
    
    # ----------------------------- PRIMITIVE TYPE --------------------------- #
    
    def visitIntType(self, ast, c): return ast
    def visitFloatType(self, ast, c): return ast
    def visitBoolType(self, ast, c): return ast
    def visitStringType(self, ast, c): return ast
    def visitVoidType(self, ast, c): return ast
    
    # ----------------------------- END PRIMITIVE TYPE --------------------------- #
    
    
    def visitId(self, ast, c):
        res = self.lookup(ast.name, sum(c, []), lambda x: x.name)
        if res and not isinstance(res.mtype, Function):
            return res.mtype
        raise Undeclared(Identifier(), ast.name)
        
    
    def visitBlock(self, ast, c):
        acc = [[]] + c 

        for i, stmt in enumerate(ast.member):

            partial_scope = sum([acc[0][:]], []) 

            if isinstance(stmt, FuncCall):
                shadow = self.lookup(stmt.funName, partial_scope, lambda x: x.name)
                if shadow and not isinstance(shadow.mtype, MType):
                    raise Undeclared(Function(), stmt.funName)

            result = self.visit(stmt, (acc, True)) if isinstance(stmt, (FuncCall, MethCall)) else self.visit(stmt, acc)
            
            if isinstance(result, Symbol):
                acc[0] = [result] + acc[0]
                
            