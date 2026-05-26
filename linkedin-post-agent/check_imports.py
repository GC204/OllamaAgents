import importlib
import sys

print('sys.executable=', sys.executable)
print('find_spec lxml_html_clean=', importlib.util.find_spec('lxml_html_clean'))
print('find_spec lxml.html.clean=', importlib.util.find_spec('lxml.html.clean'))

try:
    import lxml_html_clean
    print('lxml_html_clean package location:', getattr(lxml_html_clean, '__file__', None))
except Exception as e:
    print('lxml_html_clean import error:', repr(e))

try:
    import importlib.util as _iu
    spec = _iu.find_spec('lxml.html.clean')
    print('spec for lxml.html.clean:', spec)
except Exception as e:
    print('lxml.html.clean import error:', repr(e))
