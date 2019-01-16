import collections
import itertools

__all__ = ('Filter', 'Queue', 'Caps', 'Tee',
           'Size', 'Fraction',
           'describe', 'max_inner_size', 'min_outer_size', 'center_inside')

Fraction = collections.namedtuple('Fraction', ['num', 'den'])
Fraction.__str__ = lambda self: '%s/%s' % (self.num, self.den)

Size = collections.namedtuple('Size', ['width', 'height'])
Size.__mul__ = lambda self, arg: Size(int(arg * self.width), int(arg * self.height))
Size.__rmul__ = lambda self, arg: Size(int(arg * self.width), int(arg * self.height))
Size.__floordiv__ = lambda self, arg: Size(self.width // arg, self.height // arg)
Size.__truediv__ = lambda self, arg: Size(int(self.width / arg), int(self.height / arg))
Size.__str__ = lambda self: '%dx%d' % self

def max_inner_size(what, where):
    # Example: what=(800, 600) where=(300, 300) => (300, 225)
    return what * min(where.width / what.width, where.height / what.height)

def min_outer_size(what, where):
    # Example: what=(300, 300), where=(800, 600) => (800, 800)
    return what * max(where.width / what.width, where.height / what.height)

def center_inside(inner, outer):
    return int((outer.width - inner.width) / 2), int((outer.height - inner.height) / 2), \
           inner.width, inner.height

def join_params(params, sep=' '):
    return sep.join('%s=%s' % (k.replace('_', '-'), v) for k, v in params.items())

def join(name, sep, params, param_sep=' '):
    return name if not params else name + sep + join_params(params, param_sep)

def params_with_name(params, base, name_gens):
    if 'name' in params:
        return params
    else:
        return {**params, 'name': base + next(name_gens[base])}

def suffix_gen():
    yield ''
    for i in itertools.count(1):
        yield str(i)

class Element:
    def __init__(self, params):
        self.params = params

    def __getattr__(self, name):
        return self.params[name]

class Filter(Element):
    def __init__(self, filtername, pins=None, **params):
        super().__init__(params)
        self.filtername = filtername
        self.pins = pins

    def __str__(self):
        return join(self.filtername, ' ', self.params)

class Queue(Element):
    def __init__(self, **params):
        super().__init__(params)

    def __str__(self):
        return join('queue', ' ', self.params)

class Caps(Element):
    def __init__(self, mediatype, **params):
        super().__init__(params)
        self.mediatype = mediatype

    def __str__(self):
        return join(self.mediatype, ',', self.params, ',')

class Tee(Element):
    def __init__(self, pins=None, **params):
        super().__init__(params)
        self.pins = pins
        self.params = params

    def __str__(self):
        return join('tee', ' ', self.params)

def describe0(arg, name_gens, depth):
    recur = lambda x: describe0(x, name_gens, depth + 1)
    indent = '  ' * (depth + 1)

    if isinstance(arg, collections.Sequence):
        return ' ! '.join(recur(x) for x in arg)
    elif isinstance(arg, Tee):
        params = params_with_name(arg.params, 't', name_gens)
        return join('tee', ' ', params) + '\n' + \
             '\n'.join('%s%s. ! %s' % (indent, params['name'], recur(x)) for x in arg.pins)
    elif isinstance(arg, Filter):
        body = join(arg.filtername, ' ', arg.params)
        if arg.pins:
            params = params_with_name(arg.params, 'f', name_gens)
            return body + '\n' + \
              '\n'.join('%s%s.%s ! %s' % (indent, params['name'], pin_name, recur(x)) for pin_name, x in arg.pins.items())
        return body
    elif isinstance(arg, Queue):
        return join('queue', ' ', arg.params)
    elif isinstance(arg, Caps):
        return join(arg.mediatype, ',', arg.params, ',')
    else:
        raise ValueError('Invalid element: %s' % arg)

def describe(pipeline):
    return describe0(pipeline, collections.defaultdict(suffix_gen), 0)
