

def parseline(line):
    print repr(line)
    #XXX: should we support escaping #
    line = line.split('#')[0].rstrip()
    
    #blank lines
    if not line:
        return None, None
    # section
    if line[0] == '[' and line[-1] == ']':
        return line[1:-1], None
    # value
    elif not line[0].isspace() and '=' in line:
        name, value = line.split('=', 2)
        return name.strip(), value.strip()
    # continuation
    elif line[0].isspace():
        return None, line.strip()


def _parse(data):
    result = []
    section = None
    for line_index, line in enumerate(data.splitlines(True)):
        lineno = line_index+1

        name, data = parseline(line)
        print repr((name, data))
        if name is not None and data is not None:
            result.append((lineno, section, name, data))
        elif name is not None and data is None:
            if not name:
                raise ValueError('empty section name in line%s'%lineno)
            section = name
            result.append((lineno, section, None, None))
        elif name is None and data is not None:
            if not result:
                raise ValueError(
                    'unexpected value continuation in line %s'%lineno)

            last = result.pop()
            last_name, last_data = last[-2:]
            if last_name is None:
                raise ValueError(
                    'unexpected value continuation in line %s'%lineno)

            if last_data:
                data = '%s\n%s' % (last_data, data)
            result.append(last[:-1] + (data,))
    print result
    return result

