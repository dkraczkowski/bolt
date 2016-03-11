import inspect

def find_class(method):
    if inspect.ismethod(method):
        for cls in inspect.getmro(method.__self__.__class__):
            if cls.__dict__.get(method.__name__).__qualname__ == method.__qualname__:
                return cls

    if inspect.isfunction(method):
        return getattr(inspect.getmodule(method),
                       method.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])

    return None


def find_clsname(method):
    if inspect.ismethod(method):
        for cls in inspect.getmro(method.__self__.__class__):
            if cls.__dict__.get(method.__name__) is method:
                return inspect.getmodule(cls).__name__ + '.' + cls.__name__

    if inspect.isfunction(method):
        return inspect.getmodule(method).__name__ + '.' + \
               method.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0]

    return None


def get_fqn(obj):
    return inspect.getmodule(obj).__name__ + '.' + obj.__name__


def call_object_method(cobj, cmethod, *args, **kwargs):
    return getattr(cobj, cmethod)(*args, **kwargs)
