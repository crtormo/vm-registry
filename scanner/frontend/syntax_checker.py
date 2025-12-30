import sys

def check(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    in_backtick = False
    in_single = False
    in_double = False
    escaped = False
    
    for idx, char in enumerate(content):
        if escaped:
            escaped = False
            continue
            
        if char == '\\':
            escaped = True
            continue
            
        if char == '`' and not in_single and not in_double:
            in_backtick = not in_backtick
        elif char == "'" and not in_backtick and not in_double:
            in_single = not in_single
        elif char == '"' and not in_backtick and not in_single:
            in_double = not in_double
            
        if char == '$':
            # Check if we are in a valid state for $
            # Valid: inside backtick (template literal)
            # Invalid: inside single/double quotes (unless just text, but here we assume it points to error)
            # Invalid: in code (unless variable name, but error says Unexpected identifier, implying bad context)
            
            # Actually, standard JS allows $ in code. 
            # But the specific error 'Unexpected identifier $' often means 
            # "String" $ ...
            
            if not in_backtick and not in_single and not in_double:
                # This appears in code. 
                # Let's print it.
                line = content[:idx].count('\n') + 1
                ctx = content[max(0, idx-20):min(len(content), idx+20)].replace('\n', ' ')
                print(f"Suspicious $ at line {line}: {ctx}")

if __name__ == "__main__":
    check(sys.argv[1])
