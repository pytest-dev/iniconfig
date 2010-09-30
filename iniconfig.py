
__version__ = "1.0.dev0"

class ParseError(Exception):
    def __init__(self, lineno, msg):
        Exception.__init__(self, lineno, msg)
        self.lineno = lineno
        self.msg = msg

    def __str__(self):
        return "%s: %s" %(self.lineno, self.msg)

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
    elif line[0] == '[' or line[-1] == ']':
        raise ParseError(lineno, 'section syntax error')
    # value
    elif not line[0].isspace() and '=' in line:
        name, value = line.split('=', 2)
        return name.strip(), value.strip()
    # continuation
    elif line[0].isspace():
        return None, line.strip()
    raise ParseError(lineno, 'unexpected line: %s')


def _parse(data):
    result = []
    section = None
    for lineno, line in enumerate(data.splitlines(True)):
        name, data = parseline(line, lineno)
        # new value
        if name is not None and data is not None:
            result.append((lineno, section, name, data))
        # new section
        elif name is not None and data is None:
            if not name:
                raise ParseError(lineno, 'empty section name')
            section = name
            result.append((lineno, section, None, None))
        # continuation
        elif name is None and data is not None:
            if not result:
                raise ParseError(lineno, 'unexpected value continuation')
            last = result.pop()
            last_name, last_data = last[-2:]
            if last_name is None:
                raise ParseError(lineno, 'unexpected value continuation')

            if last_data:
                data = '%s\n%s' % (last_data, data)
            result.append(last[:-1] + (data,))
    return result


class SectionWrapper(object):
    def __init__(self, config, name):
        self.config = config
        self.name = name

    def get(self, key, default=None, convert=str):
        return self.config.get(self.name, key, convert=convert, default=default)
    def __getitem__(self, key):
        return self.config.sections[self.name][key]


    def __iter__(self):
        section = self.config.sections.get(self.name, [])
        def lineof(key):
            return self.config.lineof(self.name, key)
        for name in sorted(section, key=lineof):
            yield name

    def items(self):
        for name in self:
            yield name, self[name]



class IniConfig(object):
    def __init__(self, path=None, fp=None, data=None):
        if path:
            fp = open(path)
        if fp:
            data = fp.read()
        tokens = _parse(data)
        if tokens[0][1] is None:
            raise ParseError(tokens[0][0],
                'expected section, got name %r'%(tokens[0][2],))
        self._initialize(tokens)

    def _initialize(self, tokens):
        self._sources = {}
        self.sections = {}

        for lineno, section, name, value in tokens:
            self._sources[section, name] = lineno
            if name is None:
                if section in self.sections:
                    raise ParseError(lineno, 'duplicate section %r'%(section, ))
                self.sections[section] = {}
            else:
                if name in self.sections[section]:
                    raise ParseError(lineno, 'duplicate name %r'%(name, ))
                self.sections[section][name] = value

    def lineof(self, section, name=None):
        lineno = self._sources.get((section, name))
        if lineno is not None:
            return lineno + 1

    def get(self, section, name, default=None, convert=str):
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

    def __iter__(self):
        for name in sorted(self.sections, key=self.lineof):
            yield name

    def items(self):
        for name in self:
            yield name, SectionWrapper(self, name)
