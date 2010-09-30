import py
from iniconfig import IniConfig, ParseError

def pytest_generate_tests(metafunc):
    if 'input' in metafunc.funcargnames:
        for name, (input, expected) in check_tokens.items():
            metafunc.addcall(id=name, funcargs={
                'input': input,
                'expected': expected,
            })
    elif hasattr(metafunc.function, 'multi'):
        kwargs = metafunc.function.multi.kwargs
        names, values = zip(*kwargs.items())
        values = cartesian_product(*values)
        for p in values:
            metafunc.addcall(funcargs=dict(zip(names, p)))

def cartesian_product(L,*lists):
    # copied from http://bit.ly/cyIXjn
    if not lists:
        for x in L:
            yield (x,)
    else:
        for x in L:
            for y in cartesian_product(lists[0],*lists[1:]):
                yield (x,)+y

check_tokens = {
    'section': (
        '[section]',
        [(0, 'section', None, None)]
    ),
    'value': (
        'value = 1',
        [(0, None, 'value', '1')]
    ),
    'value in section': (
        '[section]\nvalue=1',
        [(0, 'section', None, None), (1, 'section', 'value', '1')]
    ),
    'value with continuation': (
        'names =\n Alice\n Bob',
        [(0, None, 'names', 'Alice\nBob')]
    ),
    'value with aligned continuation': (
        'names = Alice\n'
        '        Bob',
        [(0, None, 'names', 'Alice\nBob')]
    ),
    'blank line':(
        '[section]\n\nvalue=1',
        [(0, 'section', None, None), (2, 'section', 'value', '1')]
    ),
    'comment': (
        '# comment',
        []
    ),
    'comment on value': (
        'value = 1 # comment',
        [(0, None, 'value', '1')]
    ),

    'comment on section': (
        '[section] #comment',
        [(0, 'section', None, None)]
    ),

}
   
def parse(input):
    # only for testing purposes - _parse() does not use state except path
    ini = object.__new__(IniConfig)
    ini.path = "sample"
    return ini._parse(input)

def parse_a_error(input):
    return py.test.raises(ParseError, parse, input)

def test_tokenize(input, expected):
    parsed = parse(input)
    assert parsed == expected

def test_ParseError():
    e = ParseError("filename", 0, "hello")
    assert str(e) == "filename:1: hello"

def test_continuation_needs_perceeding_token():
    excinfo = parse_a_error(' Foo')
    assert excinfo.value.lineno == 0

def test_continuation_cant_be_after_section():
    excinfo = parse_a_error('[section]\n Foo')
    assert excinfo.value.lineno == 1

def test_section_cant_be_empty():
    excinfo = parse_a_error('[]')

@py.test.mark.multi(line=[
    '!!',
    '[uhm',
    'comeon]',
    '[uhm =',
    ])
def test_error_on_weird_lines(line):
    parse_a_error(line)

def test_iniconfig_from_file(tmpdir):
    path = tmpdir/'test.txt'
    path.write('[metadata]\nname=1')

    config = IniConfig(path=path)
    assert list(config.sections) == ['metadata']
    config = IniConfig(path, "[diff]")
    assert list(config.sections) == ['diff']
    py.test.raises(TypeError, "IniConfig(data=path.read())")

def test_iniconfig_section_first(tmpdir):
    excinfo = py.test.raises(ParseError, """
        IniConfig("x", data='name=1')
    """)
    assert excinfo.value.msg == "expected section, got name 'name'"

def test_iniconig_section_duplicate_fails():
    excinfo = py.test.raises(ParseError, r"""
        IniConfig("x", data='[section]\n[section]')
    """)
    assert 'duplicate section' in str(excinfo.value)

def test_iniconfig_duplicate_key_fails():
    excinfo = py.test.raises(ParseError, r"""
        IniConfig("x", data='[section]\nname = Alice\nname = bob')
    """)

    assert 'duplicate name' in str(excinfo.value)

def test_iniconfig_lineof():
    config = IniConfig("x.ini", data=
        '[section]\n'
        'value = 1\n'
        '[section2]\n'
        '# comment\n'
        'value =2'
    )

    assert config.lineof('missing') is None
    assert config.lineof('section') == 1
    assert config.lineof('section2') == 3
    assert config.lineof('section', 'value') == 2
    assert config.lineof('section2','value') == 5

def test_iniconfig_get_convert():
    config= IniConfig("x", data='[section]\nint = 1\nfloat = 1.1')
    assert config.get('section', 'int') == '1'
    assert config.get('section', 'int', convert=int) == 1

def test_iniconfig_get_missing():
    config= IniConfig("x", data='[section]\nint = 1\nfloat = 1.1')
    assert config.get('section', 'missing', default=1) == 1
    assert config.get('section', 'missing') is None

def test_section_get():
    config = IniConfig("x", data='[section]\nvalue=1')
    section = config['section']
    assert section.get('value', convert=int) == 1
    assert section.get('value', 1) == "1"
    assert section.get('missing', 2) == 2

def test_get_missing_section():
    config = IniConfig("x", data='[section]\nvalue=1')
    py.test.raises(KeyError,'config["other"]')
    config.get_section('missing') #

def test_section_getitem():
    config = IniConfig("x", data='[section]\nvalue=1')

    missing=config.get_section('test')
    py.test.raises(KeyError, 'missing["something"]')

    assert config['section']['value'] == '1'

def test_section_iter():
    config = IniConfig("x", data='[section]\nvalue=1')
    names = list(config['section'])
    assert names == ['value']
    items = list(config['section'].items())
    assert items==[('value', '1')]

def test_config_iter():
    config = IniConfig("x.ini", data='[section]\nvalue=1')
    assert list(config) == ['section']
    for name, section in config.items():
        assert section.name == name


def test_iter_file_order():
    config = IniConfig("x.ini", data="""
[section2] #cpython dict ordered before section
value = 1
value2 = 2 # dict ordered before value
[section]
a = 1
b = 2
""")
    assert list(config) == ['section2', 'section']
    assert list(config['section2']) == ['value', 'value2']
    assert list(config['section']) == ['a', 'b']


