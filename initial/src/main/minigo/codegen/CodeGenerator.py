'''
 *   @author Nguyen Hua Phung
 *   @version 1.0
 *   23/10/2015
 *   This file provides a simple version of code generator
 *
'''
from Utils import *
# from StaticCheck import *
# from StaticError import *
from Emitter import *
from Frame import Frame
from abc import ABC, abstractmethod
from functools import reduce
from Visitor import *
from AST import *
from typing import Tuple, List


class CodeGenerator(BaseVisitor,Utils):
    def __init__(self):
        self.className = "MiniGoClass"
        self.astTree = None
        self.path = None
        self.emit = None
        self.function = None
        self.list_function = []
        self.arrayCellType = None
        self.struct: StructType = None
        self.list_type = {}

    def init(self):
        mem = [
            Symbol("putInt", MType([IntType()], VoidType()), CName("io", True)),
            Symbol("putIntLn", MType([IntType()], VoidType()), CName("io", True)),
            Symbol("putFloat", MType([FloatType()], VoidType()), CName("io", True)),
            Symbol("putFloatLn", MType([FloatType()], VoidType()), CName("io", True)),
            Symbol("putBool", MType([BoolType()], VoidType()), CName("io", True)),
            Symbol("putBoolLn", MType([BoolType()], VoidType()), CName("io", True)),
            Symbol("putString", MType([StringType()], VoidType()), CName("io", True)),
            Symbol("putStringLn", MType([StringType()], VoidType()), CName("io", True)),
            Symbol("putLn", MType([], VoidType()), CName("io", True)),
            Symbol("getInt", MType([], IntType()), CName("io", True)),
            Symbol("getFloat", MType([], FloatType()), CName("io", True)),
            Symbol("getBool", MType([], BoolType()), CName("io", True)),
            Symbol("getString", MType([], StringType()), CName("io", True))
        ]
        return mem

    def gen(self, ast, dir_):
        gl = self.init()
        self.astTree = ast
        self.path = dir_
        self.emit = Emitter(dir_ + "/" + self.className + ".j")
        self.visit(ast, gl)
       
        
    def emitObjectInit(self):
        frame = Frame("<init>", VoidType())  
        self.emit.printout(self.emit.emitMETHOD("<init>", MType([], VoidType()), False, frame))
        frame.enterScope(True)  
        self.emit.printout(self.emit.emitVAR(frame.getNewIndex(), "this", ClassType(self.className), frame.getStartLabel(), frame.getEndLabel(), frame))  # Tạo biến "this" trong phương thức <init>
        
        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))
        self.emit.printout(self.emit.emitREADVAR("this", ClassType(self.className), 0, frame))  
        self.emit.printout(self.emit.emitINVOKESPECIAL(frame))  
    
        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))
        self.emit.printout(self.emit.emitRETURN(VoidType(), frame))  
        self.emit.printout(self.emit.emitENDMETHOD(frame))  
        frame.exitScope()  
        
    def emitObjectCInit(self, ast: Program, env):
        frame = Frame("<cinit>", VoidType())  
        self.emit.printout(self.emit.emitMETHOD("<clinit>", MType([], VoidType()), True, frame)) 
        frame.enterScope(True)  
        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))

        env['frame'] = frame
        self.visit(Block([Assign(Id(item.varName if isinstance(item, VarDecl) else item.conName), item.varInit if isinstance(item, VarDecl) else item.iniExpr) for item in ast.decl if isinstance(item, (VarDecl, ConstDecl))]), env)
        
        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))
        self.emit.printout(self.emit.emitRETURN(VoidType(), frame))  
        self.emit.printout(self.emit.emitENDMETHOD(frame))  
        frame.exitScope()

    def visitProgram(self, ast: Program, c):
        self.list_type = { x.name: x for x in ast.decl if isinstance(x, Type) }
        self.list_function = c + [Symbol(item.name, MType(list(map(lambda x: x.parType, item.params)), item.retType), CName(self.className)) for item in ast.decl if isinstance(item, FuncDecl)]

        for x in ast.decl:
            if isinstance(x, StructType):
                x.methods = [
                    m for m in ast.decl
                    if isinstance(m, MethodDecl) and m.recType and m.recType.name == x.name
                ]
        env ={}
        env['env'] = [c]
            
        self.emit.printout(self.emit.emitPROLOG(self.className, "java.lang.Object"))
        env = reduce(lambda a, x: self.visit(x, a) if isinstance(x, (VarDecl, ConstDecl)) else a, ast.decl, env)
        reduce(lambda a, x: self.visit(x, a) if isinstance(x, FuncDecl) else a, ast.decl, env)
        self.emitObjectInit()
        self.emitObjectCInit(ast, env)
        self.emit.printout(self.emit.emitEPILOG())
    
        
        for item in self.list_type.values():
            self.struct = item
            self.emit = Emitter(self.path + "/" + item.name + ".j")
            self.visit(item, {'env': env['env']})
        

        return env

    ## ------------------------------ DECLARATION ------------------------------ ## 
    
    def visitFuncDecl(self, ast: FuncCall, o: dict) -> dict:
        self.function = ast
        frame = Frame(ast.name, ast.retType)
        isMain = ast.name == "main"
        if isMain:
            mtype = MType([ArrayType([None],StringType())], VoidType())
            ast.body = Block([] + ast.body.member)
        else:
            mtype = MType(list(map(lambda x: x.parType, ast.params)), ast.retType)
        
        env = o.copy()
        env['frame'] = frame
        self.emit.printout(self.emit.emitMETHOD(ast.name, mtype,True, frame))
        frame.enterScope(True)
        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))
        env['env'] = [[]] + env['env']
        if isMain:
            self.emit.printout(self.emit.emitVAR(frame.getNewIndex(), "args", ArrayType([None],StringType()), frame.getStartLabel(), frame.getEndLabel(), frame))
        else:
            env = reduce(lambda acc,e: self.visit(e,acc),ast.params,env)
        self.visit(ast.body,env)
        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))
        if type(ast.retType) is VoidType:
            self.emit.printout(self.emit.emitRETURN(VoidType(), frame)) 
        self.emit.printout(self.emit.emitENDMETHOD(frame))
        frame.exitScope()
        return o
    
    def visitMethodDecl(self, ast: MethodDecl, o):
        self.function = ast.fun
        frame = Frame(ast.fun.name, ast.fun.retType)
        mtype = MType([param.parType for param in ast.fun.params], ast.fun.retType)
        
        env = o.copy()
        env['frame'] = frame
        self.emit.printout(self.emit.emitMETHOD(ast.fun.name, mtype,False, frame))
        frame.enterScope(True)
        rec_type = ast.recType.name if ast.recType else self.struct.name
        frame.getNewIndex()
        self.emit.printout(self.emit.emitVAR(0, "this", Id(rec_type), frame.getStartLabel(), frame.getEndLabel(), frame)) 
        receiver_symbol = Symbol(ast.receiver, Id(rec_type), Index(0))
        env['env'][0].append(receiver_symbol)
        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))
        if ast.receiver is None:
            rec_type = ast.recType.name if ast.recType else self.struct.name
            self.emit.printout(self.emit.emitREADVAR("this", Id(rec_type), 0, frame))
            self.emit.printout(self.emit.emitINVOKESPECIAL(frame))  

        env['env'] = [[]] + env['env']
        env = reduce(lambda acc,e: self.visit(e,acc),ast.fun.params,env) 
        self.visit(ast.fun.body,env)
        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))
        if type(ast.fun.retType) is VoidType:
            self.emit.printout(self.emit.emitRETURN(VoidType(), frame))  
        self.emit.printout(self.emit.emitENDMETHOD(frame))
        frame.exitScope()
        return o

    def visitParamDecl(self, ast: ParamDecl, o: dict) -> dict:
        frame = o['frame']
        index = frame.getNewIndex()
        o['env'][0].append(Symbol(ast.parName, ast.parType, Index(index)))
        self.emit.printout(self.emit.emitVAR(index, ast.parName, ast.parType, frame.getStartLabel() ,frame.getEndLabel(), frame))     
        return o

    def visitVarDecl(self, ast: VarDecl, o: dict) -> dict:
        varInit = ast.varInit
        varType = ast.varType
        
        def create_init(varType: Type, o: dict):
            if type(varType) is IntType:
                return IntLiteral(0)
            elif type(varType) is FloatType:
                return FloatLiteral(0.0)
            elif type(varType) is BoolType:
                return BooleanLiteral('false')
            elif type(varType) is StringType:
                return StringLiteral("\"\"")
            elif type(varType) is ArrayType:
                resolved_dims = []
                for dim in varType.dimens:
                    if isinstance(dim, IntLiteral): 
                        resolved_dims.append(dim.value)
                    elif isinstance(dim, Id):
                        resolved_dims.append(1) 
                    else:
                        resolved_dims.append(1)

                def build_array_literal(dims: list, eleType: Type):
                    if not dims:
                        if isinstance(eleType, IntType):
                            return IntLiteral(0)
                        elif isinstance(eleType, FloatType):
                            return FloatLiteral(0.0)
                        elif isinstance(eleType, BoolType):
                            return BooleanLiteral('false')
                        elif isinstance(eleType, StringType):
                            return StringLiteral("\"\"")
                    else:
                        return [build_array_literal(dims[1:], eleType) for _ in range(dims[0])]

                init_value = build_array_literal(resolved_dims, varType.eleType)
                return ArrayLiteral(varType.dimens, varType.eleType, init_value)
            elif type(varType) is StructType or type(varType) is Id:
                return StructLiteral(varType.name, [])
      
               
        
        if not varInit:
            varInit = create_init(varType, o)
            # if type(varType) is ArrayType:
            #     ast.varInit = varInit
            ast.varInit = varInit

            

        env = o.copy()
        env['frame'] = Frame("<frame>", VoidType()) 
        rhsCode, rhsType = self.visit(varInit, env)
        

        if not varType:
            varType = rhsType
            
        if isinstance(varType, StructType):
            varType = Id(varType.name)
            
        
        if 'frame' not in o: 
            o['env'][0].append(Symbol(ast.varName, varType, CName(self.className)))
            self.emit.printout(self.emit.emitATTRIBUTE(ast.varName, varType, True, False, None))
        else:
            frame = o['frame']
            index = frame.getNewIndex()
            o['env'][0].append(Symbol(ast.varName, varType, Index(index)))
            self.emit.printout(self.emit.emitVAR(index, ast.varName, varType, frame.getStartLabel(), frame.getEndLabel(), frame)) 

            rhsCode, rhsType = self.visit(varInit, o)
            
            if type(varType) is FloatType and type(rhsType) is IntType:
                rhsCode = rhsCode + self.emit.emitI2F(frame)

            self.emit.printout(rhsCode)
            self.emit.printout(self.emit.emitWRITEVAR(ast.varName, varType, index,  frame))                    
        return o
    
    def visitConstDecl(self, ast:ConstDecl, o: dict) -> dict:
        return self.visit(VarDecl(ast.conName, ast.conType, ast.iniExpr), o)
    
    ## ------------------------------ END DECLARATION ------------------------------ ## 
    
    
    ## ------------------------------ STATEMENT ------------------------------ ## 
    
    def visitFuncCall(self, ast: FuncCall, o: dict) -> dict:
        sym = next(filter(lambda x: x.name == ast.funName, self.list_function),None)
        env = o.copy()
        if o.get('stmt'):
            o["stmt"] = False
            
            
            # for x in ast.args:
            #     result = self.visit(x, env)
            #     if isinstance(result, tuple):
            #         code, _ = result
            #         self.emit.printout(code)
            [self.emit.printout(self.visit(x,env)[0]) for x in ast.args if isinstance(self.visit(x, env), tuple)] 
            
            
            self.emit.printout(self.emit.emitINVOKESTATIC(f"{sym.value.value}/{ast.funName}",sym.mtype, o['frame']))
            return o 
        output = "".join([str(self.visit(x, env)[0]) for x in ast.args])
        output += self.emit.emitINVOKESTATIC(f"{sym.value.value}/{ast.funName}",sym.mtype, o['frame']) 
        return output, sym.mtype.rettype
    
    def visitMethCall(self, ast:MethCall, o: dict) -> tuple[str, Type]:
        # class MethCall(Expr,Stmt):
        #     receiver: Expr
        #     metName: str
        #     args:List[Expr]

        code, typ = self.visit(ast.receiver, o)
        if isinstance(typ, Id):
            typ = self.list_type.get(typ.name)
        
       
        
            
        is_stmt = o.pop("stmt", False)    
        returnType = None
        if type(typ) is StructType:
            for item in ast.args:
                code += self.visit(item, o)[0]

            method = next(m for m in typ.methods if m.fun.name == ast.metName)
            mtype = MType([item.parType for item in method.fun.params], method.fun.retType)
            returnType = method.fun.retType
            code += self.emit.emitINVOKEVIRTUAL(typ.name + '/' + method.fun.name, mtype, o['frame']) 

        elif type(typ) is InterfaceType:
            for item in ast.args:
                code += self.visit(item, o)[0] 
            method = next(m for m in typ.methods if m.name == ast.metName) 
            mtype = MType(method.params, method.retType)
            returnType = method.retType
            code += self.emit.emitINVOKEINTERFACE(typ.name + '/' + method.name, mtype, o['frame']) 

        if is_stmt:
            self.emit.printout(code)
            return o

        return code, returnType

    def visitAssign(self, ast: Assign, o: dict) -> dict:
        if type(ast.lhs) is Id and not next(filter(lambda x: x.name == ast.lhs.name, [j for i in o['env'] for j in i]),None):
            return self.visitVarDecl(VarDecl(ast.lhs.name, None, ast.rhs), o)
        rhsCode, rhsType = self.visit(ast.rhs, o)
        o['isLeft'] = True
        lhsCode, lhsType= self.visit(ast.lhs, o)
        o['isLeft'] = False

        if type(lhsType) is FloatType and type(rhsType) is IntType:
            rhsCode = rhsCode + self.emit.emitI2F(o['frame'])
            
        
        o['frame'].push()
        o['frame'].push()
        
        if type(ast.lhs) is FieldAccess:
            self.emit.printout(lhsCode)  
            self.emit.printout(rhsCode) 
            self.emit.printout(self.emit.emitPUTFIELD(self.struct.name + '/' + ast.lhs.field, lhsType, o['frame']))
        elif type(ast.lhs) is ArrayCell:
            self.emit.printout(lhsCode)
            self.emit.printout(rhsCode)
            self.emit.printout(self.emit.emitASTORE(self.arrayCellType, o['frame']))
        else:
            self.emit.printout(rhsCode) 
            self.emit.printout(lhsCode)
        return o

    def visitReturn(self, ast: Return, o: dict) -> dict:
        if ast.expr:
            expr, typ = self.visit(ast.expr, o)
            self.emit.printout(expr)
            self.emit.printout(self.emit.emitRETURN(typ, o['frame']))
        else: 
            self.emit.printout(self.emit.emitRETURN(VoidType(), o['frame'])) 
        return o
    
    def visitIf(self, ast: If, o: dict) -> dict:
        frame = o['frame']
        label_exit = frame.getNewLabel()
        label_end_if = frame.getNewLabel()
        condCode, _ = self.visit(ast.expr, o)
        self.emit.printout(condCode)
        self.emit.printout(self.emit.emitIFFALSE(label_end_if, frame))
        self.visit(ast.thenStmt, o)
        self.emit.printout(self.emit.emitGOTO(label_exit, frame))
        self.emit.printout(self.emit.emitLABEL(label_end_if, frame))

        if ast.elseStmt is not None:
            self.visit(ast.elseStmt, o)
        self.emit.printout(self.emit.emitLABEL(label_exit, frame))
        return o
    

    def visitForBasic(self, ast: ForBasic, o: dict) -> dict:
        # class ForBasic(Stmt):
        #     cond:Expr
        #     loop:Block
        frame = o['frame']
        frame.enterLoop()
        lable_new = frame.getNewLabel()
        lable_Break = frame.getBreakLabel() 
        lable_Cont = frame.getContinueLabel()
        self.emit.printout(self.emit.emitLABEL(lable_new, frame))
        self.emit.printout(self.visit(ast.cond, o)[0])
        self.emit.printout(self.emit.emitIFFALSE(lable_Break, frame))
        self.visit(ast.loop, o)
        self.emit.printout(self.emit.emitLABEL(lable_Cont, frame))
        self.emit.printout(self.emit.emitGOTO(lable_new, frame))
        self.emit.printout(self.emit.emitLABEL(lable_Break, frame))
        frame.exitLoop()
        return o
    
    def visitForStep(self, ast: ForStep, o: dict) -> dict:
        
        # class ForStep(Stmt):
        #     init:Stmt
        #     cond:Expr
        #     upda:Assign
        #     loop:Block
        frame = o['frame']
        frame.enterLoop()
        env = o.copy()
        env['env'] = [[]] + env['env']
        lable_new = frame.getNewLabel()
        lable_break = frame.getBreakLabel()
        lable_cont = frame.getContinueLabel()
        self.visit(ast.init, env)
        self.emit.printout(self.emit.emitLABEL(lable_new, frame))
        self.emit.printout(self.visit(ast.cond, env)[0])
        self.emit.printout(self.emit.emitIFFALSE(lable_break, frame))
        self.visit(ast.loop, env)
        self.emit.printout(self.emit.emitLABEL(lable_cont, frame))
        self.visit(ast.upda, env)
        self.emit.printout(self.emit.emitGOTO(lable_new, frame))
        self.emit.printout(self.emit.emitLABEL(lable_break, frame))
        frame.exitLoop()
        return o

    def visitForEach(self, ast, o: dict) -> dict:
        return o 
    def visitContinue(self, ast, o: dict) -> dict:
        self.emit.printout(self.emit.emitGOTO(o['frame'].getContinueLabel(), o['frame'])) 
        return o

    def visitBreak(self, ast, o: dict) -> dict:
        self.emit.printout(self.emit.emitGOTO(o['frame'].getBreakLabel(), o['frame']))
        return o

    ## ------------------------------ END STATEMENT ------------------------------ ## 


    ## ------------------------------ OPERATION ------------------------------ ## 
    def visitBinaryOp(self, ast: BinaryOp, o: dict) -> tuple[str, Type]:
        op = ast.op
        frame = o['frame']
        codeLeft, typeLeft = self.visit(ast.left, o)
        codeRight, typeRight = self.visit(ast.right, o)
        if op in ['+', '-'] and type(typeLeft) in [FloatType, IntType]:
            typeReturn = IntType() if type(typeLeft) is IntType and type(typeRight) is IntType else FloatType()
            if type(typeReturn) is FloatType:
                if type(typeLeft) is IntType:
                    codeLeft += self.emit.emitI2F(frame)
                if type(typeRight) is IntType:
                    codeRight += self.emit.emitI2F(frame)
                
            return codeLeft + codeRight + self.emit.emitADDOP(op, typeReturn, frame), typeReturn 
        if op in ['*', '/']:
            typeReturn = IntType() if type(typeLeft) is IntType and type(typeRight) is IntType else FloatType() 
            if type(typeReturn) is FloatType:
                if type(typeLeft) is IntType:
                    codeLeft += self.emit.emitI2F(frame)
                if type(typeRight) is IntType:
                    codeRight += self.emit.emitI2F(frame)
            return codeLeft + codeRight + self.emit.emitMULOP(op, typeReturn, frame), typeReturn 
        if op in ['%']:
            return codeLeft + codeRight + self.emit.emitMOD(frame), IntType()
        if op in ['==', '!=', '<', '>', '>=', '<='] and type(typeLeft) in [FloatType, IntType]:
            typeReturn = IntType() if type(typeLeft) is IntType and type(typeRight) is IntType else FloatType()
            return codeLeft + codeRight + self.emit.emitREOP(op, typeReturn, frame), BoolType() 
        if op in ['||']:
            # return codeLeft + codeRight + self.emit.emitOROP(frame), BoolType()
            
            label_true = frame.getNewLabel()
            label_end = frame.getNewLabel()

            code = codeLeft
            code += self.emit.emitIFTRUE(label_true, frame)  
            code += codeRight
            code += self.emit.emitIFTRUE(label_true, frame)  
            code += self.emit.emitPUSHCONST("0", BoolType(), frame)
            code += self.emit.emitGOTO(label_end, frame)
            code += self.emit.emitLABEL(label_true, frame)
            code += self.emit.emitPUSHCONST("1", BoolType(), frame)
            code += self.emit.emitLABEL(label_end, frame)
            return code, BoolType()
            
        if op in ['&&']:
            # return codeLeft + codeRight + self.emit.emitANDOP(frame), BoolType()  
            
            label_false = frame.getNewLabel()
            label_end = frame.getNewLabel()

            code = codeLeft
            code += self.emit.emitIFFALSE(label_false, frame) 
            code += codeRight
            code += self.emit.emitIFFALSE(label_false, frame) 
            code += self.emit.emitPUSHCONST("1", BoolType(), frame) 
            code += self.emit.emitGOTO(label_end, frame)
            code += self.emit.emitLABEL(label_false, frame)
            code += self.emit.emitPUSHCONST("0", BoolType(), frame)
            code += self.emit.emitLABEL(label_end, frame)
            return code, BoolType()

        # string        
        if op in ['+', '-'] and type(typeLeft) in [StringType]:
            concatType = MType([StringType()], StringType())
            return codeLeft + codeRight + self.emit.emitINVOKEVIRTUAL("java/lang/String/concat", concatType, frame), StringType() 
        if op in ['==', '!=', '<', '>', '>=', '<='] and type(typeLeft) in [StringType]:
            compareType = MType([StringType()], IntType())
            code = codeLeft + codeRight + self.emit.emitINVOKEVIRTUAL("java/lang/String/compareTo", compareType, frame)
            code += self.emit.emitPUSHICONST(0, frame)
            code = code + self.emit.emitREOP(op, IntType(), frame)
            return code, BoolType() 
              
    def visitUnaryOp(self, ast: UnaryOp, o: dict) -> tuple[str, Type]:
        if ast.op == '!':
            code, type_return = self.visit(ast.body, o)
            return code + self.emit.emitNOT(BoolType(), o['frame']), BoolType()

        if ast.op == '-':
            code, type_return = self.visit(ast.body, o)
            return code + self.emit.emitNEGOP(type_return, o['frame']), type_return
        
    ## ------------------------------ END OPERATION ------------------------------ ## 
    
    
    ## ------------------------------ LITERAL ------------------------------ ## 
    
    def visitIntLiteral(self, ast: IntLiteral, o: dict) -> tuple[str, Type]:
        return self.emit.emitPUSHICONST(ast.value, o['frame']), IntType()
    
    def visitFloatLiteral(self, ast: FloatLiteral, o: dict) -> tuple[str, Type]:
        return self.emit.emitPUSHFCONST(ast.value, o['frame']), FloatType()
    
    def visitBooleanLiteral(self, ast: BooleanLiteral, o: dict) -> tuple[str, Type]:
        return self.emit.emitPUSHICONST(ast.value, o['frame']), BoolType()
    
    def visitStringLiteral(self, ast: StringLiteral, o: dict) -> tuple[str, Type]:

        return self.emit.emitPUSHCONST(ast.value, StringType(), o['frame']), StringType()
    
    def visitNilLiteral(self, ast:NilLiteral, o: dict) -> tuple[str, Type]:
        return self.emit.emitPUSHNULL(o['frame']), Id("")  
    
    ## ------------------------------ END LITERAL ------------------------------ ## 
    
    
    ## ------------------------------ ARRAY ------------------------------ ## 
    
    def visitArrayCell(self, ast: ArrayCell, o: dict) -> tuple[str, Type]:
        newO = o.copy()
        newO['isLeft'] = False
        codeGen, arrType = self.visit(ast.arr, newO) 

        for idx, item in enumerate(ast.idx):
            codeGen += self.visit(item, newO)[0] 
            if idx != len(ast.idx) - 1:
                codeGen += self.emit.emitALOAD(arrType, o['frame'])

        retType = None
        if len(arrType.dimens) == len(ast.idx):
            retType = arrType.eleType
            if not o.get('isLeft'):
                codeGen += self.emit.emitALOAD(retType, o['frame']) 
            else:
                self.arrayCellType = retType
        else:
            retType = ArrayType(arrType.dimens[len(ast.idx): ], arrType.eleType)
            if not o.get('isLeft'):
                codeGen += self.emit.emitALOAD(retType, o['frame']) 
            else:
                self.arrayCellType = retType
                
        return (codeGen, retType)
    
    def visitArrayLiteral(self, ast:ArrayLiteral , o: dict) -> tuple[str, Type]:
        
        if isinstance(ast.value, Id):
            return self.visit(ast.value, o)
        
        def nested2recursive(dat: Union[Literal, list['NestedList']], o: dict) -> tuple[str, Type]:
            if not isinstance(dat,list): 
                return self.visit(dat, 0) 

            frame = o['frame']
            dim = len(dat)
            codeGen = self.emit.emitPUSHCONST(dim, IntType(), frame) 
            if not isinstance(dat[0],list):
                _, type_element_array = self.visit(dat[0], o)
                if type(type_element_array) is not ArrayType:
                    codeGen += self.emit.emitNEWARRAY(type_element_array, frame)
                else: 
                    codeGen += self.emit.emitANEWARRAY(type_element_array, frame)
                for idx, item in enumerate(dat):
                    codeGen += self.emit.emitDUP(frame)
                    codeGen += self.emit.emitPUSHCONST(idx, IntType(), frame)
                    codeGen += self.visit(item, o)[0] 
                    codeGen += self.emit.emitASTORE(type_element_array, frame)
                return codeGen, ArrayType([len(dat)], type_element_array)

            _, type_element_array = nested2recursive(dat[0], o)
            if type(type_element_array) is not ArrayType:
                codeGen += self.emit.emitNEWARRAY(type_element_array, frame)
            else: 
                codeGen += self.emit.emitANEWARRAY(type_element_array, frame)
                
            for idx, item in enumerate(dat):
                codeGen += self.emit.emitDUP(frame)
                codeGen += self.emit.emitPUSHCONST(idx, IntType(), frame) 
                codeGen += nested2recursive(item, o)[0] 
                codeGen += self.emit.emitASTORE(type_element_array, frame) 
            return codeGen, ArrayType([len(dat)] + type_element_array.dimens, type_element_array.eleType)
        
        if type(ast.value) is ArrayType:
            return self.visit(ast.value, o)
        
        return nested2recursive(ast.value, o)
    
    def visitArrayType(self, ast:ArrayType, o):
        codeGen += "".join([self.visit(dim, o)[0] for dim in ast.dimens])
        codeGen += self.emit.emitMULTIANEWARRAY(ast, o['frame'])
        return codeGen, ast

    ## ------------------------------ END ARRAY ------------------------------ ## 
    
    
    ## ------------------------------ STRUCT ------------------------------ ## 
    
    def visitStructLiteral(self, ast:StructLiteral, o: dict) -> tuple[str, Type]:
        code = self.emit.emitNEW(ast.name, o['frame'])
        code += self.emit.emitDUP(o['frame'])
        list_type = []
        for item in ast.elements:
            c, t = self.visit(item[1], o)
            code += c 
            list_type += [t]
        code += self.emit.emitINVOKESPECIAL(o['frame'], ast.name + '/' + "<init>", MType(list_type, VoidType()) if len(ast.elements) else MType([], VoidType()))
        return code, Id(ast.name)

    def visitStructType(self, ast: StructType, o):
        # ast.methods = [m for m in self.astTree.decl if isinstance(m, MethodDecl) and m.recType and m.recType.name == ast.name]


        self.emit.printout(self.emit.emitPROLOG(ast.name, "java.lang.Object")) 
        for item in self.list_type.values():
            if isinstance(item, InterfaceType) and item.name != ast.name:# self.checkType(item, ast, [(InterfaceType, StructType)]):
                self.emit.printout(self.emit.emitIMPLEMENTS(item.name))
        

        for item in ast.elements:
            self.emit.printout(self.emit.emitATTRIBUTE(item[0], item[1], False, False, None)) 
        
        self.visit(MethodDecl(None, None, FuncDecl("<init>", [ParamDecl(item[0], item[1]) for item in ast.elements], VoidType(),
                            Block([Assign(FieldAccess(Id("this"), item[0]), Id(item[0])) for item in ast.elements]))), o)
        self.visit(MethodDecl(None, None, FuncDecl("<init>", [], VoidType(), Block([]))), o)
        for item in ast.methods: self.visit(item, o)
        self.emit.printout(self.emit.emitEPILOG()) 
        
    def visitFieldAccess(self, ast:FieldAccess, o: dict) -> tuple[str, Type]:
        # class FieldAccess(LHS):
        #     receiver:Expr
        #     field:str
        code, typ = self.visit(ast.receiver, o)
        # typ = self.list_type[typ.name]
        # typ = self.list_type.get(typ.name)
        typ = self.struct if self.struct is not None else self.list_type.get(typ.name)
        field = next(item for item in typ.elements if item[0] == ast.field)
        if o.get("isLeft"): 
            return code, field[1] 
        else:
            return code + self.emit.emitGETFIELD(f"{typ.name}/{ast.field}", field[1], o["frame"]), field[1]
           
    ## ------------------------------ END STRUCT ------------------------------ ##                  
    def visitInterfaceType(self, ast: InterfaceType, o):
        self.emit.printout(self.emit.emitPROLOG(ast.name, "java.lang.Object", True))
    
        for method in ast.methods:
            mtype = MType(method.params, method.retType)
            frame = Frame(method.name, method.retType)
            self.emit.printout(self.emit.emitMETHOD(method.name, mtype, False, frame, isAbstract=True))
            # self.emit.printout(self.emit.emitENDMETHOD(frame))
            self.emit.printout(self.emit.emitENDMETHOD2(frame))
        self.emit.printout(self.emit.emitEPILOG())

    
    def checkType(self, LHS_type: Type, RHS_type: Type, list_type_permission: List[Tuple[Type, Type]] = []) -> bool:
        if type(RHS_type) == StructType and RHS_type.name == "":
            if type(LHS_type) in [Id,StructType,InterfaceType]:
                return True

        LHS_type = self.lookup(LHS_type.name, self.list_type.values(), lambda x: x.name == LHS_type.name) if isinstance(LHS_type, Id) else LHS_type
        RHS_type = self.lookup(RHS_type.name, self.list_type.values(), lambda x: x.name == LHS_type.name) if isinstance(RHS_type, Id) else RHS_type
        
        

        # if (type(LHS_type), type(RHS_type)) in list_type_permission:
        if isinstance(LHS_type, InterfaceType) and isinstance(RHS_type, StructType) and (InterfaceType, StructType) in list_type_permission:

            if isinstance(LHS_type, InterfaceType) and isinstance(RHS_type, StructType):
                return all(
                    any(
                        struct_methods.fun.name == inteface_method.name and
                        self.checkType(struct_methods.fun.retType, inteface_method.retType) and
                        len(struct_methods.fun.params) == len(inteface_method.params) and
                        reduce(
                            lambda x, i: x and self.checkType(struct_methods.fun.params[i].parType, inteface_method.params[i]),
                            range(len(struct_methods.fun.params)),
                            True
                        )
                        for struct_methods in RHS_type.methods
                    )
                    for inteface_method in LHS_type.methods
                )
            if isinstance(LHS_type, (StructType, InterfaceType)) and isinstance(RHS_type, (InterfaceType, StructType)):
                return LHS_type.name == RHS_type.name

        if isinstance(LHS_type, ArrayType) and isinstance(RHS_type, ArrayType):
            return (len(LHS_type.dimens) == len(RHS_type.dimens)
                    and all(
                        l.value == r.value  for l, r in zip(LHS_type.dimens, RHS_type.dimens)
                    )
                    and self.checkType(LHS_type.eleType, RHS_type.eleType, [list_type_permission[0]] if len(list_type_permission) != 0 else []))
        return type(LHS_type) == type(RHS_type) and type(LHS_type) in [IntType, FloatType, StringType, BoolType]
    
    
    
    


    
    ## ------------------------------ ID AND BLOCK ------------------------------ ## 
    
    def visitBlock(self, ast: Block, o: dict) -> dict:
        
        env = o.copy()
        env['env'] = [[]] + env['env']
        frame = env['frame']
        frame.enterScope(False)
        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))
        for item in ast.member:
            
            if type(item) is FuncCall:
                env["stmt"] = True
            elif type(item) is MethCall:
                env["stmt"] = True
            env = self.visit(item, env)

        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))
        frame.exitScope()
        return o
    
    
    def visitId(self, ast: Id, o: dict) -> tuple:
        sym = next(filter(lambda x: x.name == ast.name, [j for i in o['env'] for j in i]),None)
        # sym = next((s for env in o['env'] for s in env if s.name == ast.name), None)
        if sym is None:
            struct_type = self.list_type.get(self.struct.name)

            if o.get('isLeft'):
                return self.emit.emitREADVAR("this", Id(self.struct.name), 0, o['frame']), Id(self.struct.name)
            field = next((item for item in struct_type.elements if item[0] == ast.name), None)
            return (
                self.emit.emitREADVAR("this", Id(self.struct.name), 0, o['frame']) +
                self.emit.emitGETFIELD(f"{self.struct.name}/{ast.name}", field[1], o['frame']),
                field[1])
            
        
        
        
        if o.get('isLeft'):
            if type(sym.value) is Index:
                return self.emit.emitWRITEVAR(ast.name, sym.mtype, sym.value.value, o['frame']), sym.mtype
            else:   
                return self.emit.emitPUTSTATIC(sym.value.value + '/' + ast.name, sym.mtype, o['frame']),sym.mtype       
        if type(sym.value) is Index:
            return self.emit.emitREADVAR(Id(ast.name), sym.mtype, sym.value.value, o['frame']), sym.mtype 
        else:         
            return self.emit.emitGETSTATIC(sym.value.value + '/' + ast.name, sym.mtype, o['frame']), sym.mtype 
            
