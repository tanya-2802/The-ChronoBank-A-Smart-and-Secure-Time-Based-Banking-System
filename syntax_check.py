import ast

def check_syntax(file_path):
    try:
        with open(file_path, 'r') as file:
            source = file.read()
        
        ast.parse(source)
        print(f"SUCCESS: No syntax errors detected in {file_path}")
        return True
    except SyntaxError as e:
        print(f"ERROR: Syntax error in {file_path}:")
        print(f"  Line {e.lineno}, Column {e.offset}")
        print(f"  {e.text.strip()}")
        print(f"  {' ' * (e.offset - 1)}^")
        print(f"  {e.msg}")
        return False

if __name__ == "__main__":
    file_path = "f:/DAIICT/Sem 2/OOPs/chronobank/app/services/fraud_detection.py"
    check_syntax(file_path)