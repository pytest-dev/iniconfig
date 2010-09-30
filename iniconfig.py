
__version__ = "1.0"

def parseline(line, lineno):
    
    # comments
    #XXX: should we support escaping #
    line = line.split('#')[0].rstrip()

    # blank lines
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
    raise ValueError('unexpected line %s %r'%(lineno, line))


def _parse(data):
    result = []
    section = None
    for line_index, line in enumerate(data.splitlines(True)):
        lineno = line_index+1

        name, data = parseline(line, lineno)
        # new value
        if name is not None and data is not None:
            result.append((lineno, section, name, data))
        # new section
        elif name is not None and data is None:
            if not name:
                raise ValueError('empty section name in line%s'%lineno)
            section = name
            result.append((lineno, section, None, None))
        # continuation
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
    return result

class SectionWrapper(object):
    def __init__(self, config, name):
        self.config = config
        self.name = name

    def get(self, key, convert=str, default=None):
        return self.config.get(self.name, key, convert=convert, default=default)

class IniConfig(object):
    def __init__(self, path=None, fp=None, data=None):
        if path:
            fp = open(path)
        if fp:
            data = fp.read()
        tokens = _parse(data)
        if tokens[0][1] is None:
            raise ValueError('expected section in line %s, got name %r'%(
                tokens[0][0],
                tokens[0][2],
            ))
        self._initialize(tokens)

    def _initialize(self, tokens):
        self._sources = {}
        self.sections = {}

        for line, section, name, value in tokens:
            self._sources[section, name] = line
            if name is None:
                if section in self.sections:
                    raise ValueError(
                        'duplicate section %r in line %s'%(section, line)
                    )
                self.sections[section] = {}
            else:
                if name in self.sections[section]:
                    raise ValueError(
                        'duplicate value %r in line %s'%(name, line)
                    )
                self.sections[section][name] = value

    def lineof(self, section, name=None):
        return self._sources.get((section, name))

    def get(self, section, name, convert=str, default=None):
        try:
            return convert(self.sections[section][name])
        except KeyError:
            return default

    def __getitem__(self, name):
        if name not in self.sections:
            raise KeyError(name)
        return SectionWrapper(self, name)

    def get_section(self, name):
        return SectionWrapper(self, name)
