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
        [ (1, 'section', None, None)]
    ),
    'value': (
        'value = 1',
        [(1, None, 'value', '1')]
    ),
    'value in section': (
        '[section]\nvalue=1',
        [(1, 'section', None, None), (2, 'section', 'value', '1')]
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

