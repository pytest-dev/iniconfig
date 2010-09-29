import py
from iniconfig import _parse as parse


def pytest_funcarg__tokens(request):
    """
    * detend the docstring
    * strip the leading line
    * parse to tokens
    """
    doc = request.function.__doc__
    doc = py.std.textwrap.dedent(doc)
    return parse(doc.lstrip())


parsings = {
    'section': (
        '[section]',
        [(1, 'section', None, None)]
    ),
    'value': (
        'value = 1',
        [(1, None, 'value', '1')]
    ),
    'value in section': (
        '[section]\nvalue=1',
        [(1, 'section', None, None), (2, 'section', 'value', '1')]
    ),
    'value with continuation': (
        'names =\n Alice\n Bob',
        [(1, None, 'names', 'Alice\nBob')]
    ),
    'value with aligned continuation': (
        'names = Alice\n'
        '        Bob',
        [(1, None, 'names', 'Alice\nBob')]
    ),
    'blank line':(
        '[section]\n\nvalue=1',
        [(1, 'section', None, None), (3, 'section', 'value', '1')]
    ),
    'comment': (
        '# comment',
        []
    ),
    'comment on value': (
        'value = 1 # comment',
        [(1, None, 'value', '1')]
    ),

    'comment on section': (
        '[section] #comment',
        [(1, 'section', None, None)]
    ),



}

def pytest_generate_tests(metafunc):
    if 'input' in metafunc.funcargnames:
        for name, (input, expected) in parsings.items():
            metafunc.addcall(id=name, funcargs={
                'input': input,
                'expected': expected,
            })



def test_parse(input, expected):
    parsed = parse(input)
    assert parsed == expected


def test_continuation_needs_perceeding_token():
    with py.test.raises(ValueError) as excinfo:
        parse(' Foo')
    assert 'line 1' in excinfo.value.args[0]

def test_continuation_cant_be_after_section():
    with py.test.raises(ValueError) as excinfo:
        parse('[section]\n Foo')
    assert 'line 2' in excinfo.value.args[0]

def test_section_cant_be_empty():
    with py.test.raises(ValueError) as excinfo:
        parse('[]')

def test_cant_handle_weird_lines():
    with py.test.raises(ValueError) as excinfo:
        parse('!!')
