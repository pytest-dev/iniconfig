

def parseline(line):
    print repr(line)
    line = line.rstrip()
    # section
    if line[0] == '[' and line[-1] == ']':
        return line[1:-1], None
    elif not line[0].isspace() and '=' in line:
        name, value = line.split('=', 2)
        return name.strip(), value.strip()
        

    return None, None

def _parse(data):
    result = []
    section = None
    for line_index, line in enumerate(data.splitlines(True)):
        lineno = line_index+1

        name, data = parseline(line)
        print repr((name, data))
        if data is None:
            section = name
            result.append((lineno, section, None, None))
        else:
            result.append((lineno, section, name, data))
    print result
    return result

