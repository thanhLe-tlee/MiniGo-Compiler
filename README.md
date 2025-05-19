# MiniGo Compiler Project 

**Course**: Principles of Programming Languages (CO3005)  
**University**: Ho Chi Minh City University of Technology (HCMUT)  
**Semester**: Spring 2025 

## 🗂️ Project Folder Structure

<pre> Folder PATH listing for volume DATA
Volume serial number is 7E6E-9FD8
D:.
+---.vscode
+---src
|   +---external
|   +---lib
|   +---main
|   |   \---minigo
|   |       +---astgen
|   |       |   \---__pycache__
|   |       +---checker
|   |       |   \---__pycache__
|   |       +---codegen
|   |       |   \---__pycache__
|   |       +---parser
|   |       |   +---.antlr
|   |       |   \---__pycache__
|   |       \---utils
|   |           \---__pycache__
|   \---test
|       +---solutions
|       |   +---501
|       |   +---502
|       |   +---503
|       |   +---504
|       |   +---505
|       |   \---506
|       +---testcases
|       \---__pycache__
\---target
 </pre>

---

## 📌 Description
- This is a simplified version of Go programming language, designed for students to practice building a compiler. It retains the core concepts of Go, such as basic data types, structs and interfaces. The goal of this project was to understand how a compiler works from scratch and apply theoretical knowledge into practice by building each stage step by step.

- In this project, the compiler supports key phases of compilation, including:
- **Lexical Analysis**
- **Parsing** (Abstract Syntax Tree construction)
- **Semantic Analysis**
- **Intermediate Code Generation**

---

## 🛠️ Technologies Used

- **Python 3**
- Custom grammar for MiniGo
- Internal testing and code generation tools

---

## 🚀 How to Run

```bash
# Step 1: Change to the source directory
cd initial/src

# Step 2: Generate intermediate files (e.g., AST, IR)
python run.py gen

# Step 3: Run tests with provided test suites
python run.py test CodeGenSuite




