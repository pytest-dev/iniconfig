import py
from iniconfig import _parse as parse


check_tokens = {
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


weird_lines = [
    '!!',
    '[uhm',
    'comeon]',
    '[uhm =',
    'comeon] =',
]

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
        
        def toseq(item):
            if not isinstance(item, (list, tuple)):
                return item,
            else:
                return item
        from itertools import product

        values = product(*map(toseq, values))
        for p in values:
            metafunc.addcall(funcargs=dict(zip(names, p)))




def test_tokenize(input, expected):
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


@py.test.mark.multi(line=weird_lines)
def test_error_on_weird_lines(line):
    with py.test.raises(ValueError) as excinfo:
        parse('!!')
