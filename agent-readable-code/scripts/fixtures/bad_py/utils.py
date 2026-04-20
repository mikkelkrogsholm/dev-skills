"""Dumping-ground module. Should trigger AR003 on filename,
AR003 on class/function names, AR004 on metaprogramming,
AR005 on deep inheritance, AR006 on untyped public functions."""

import importlib


# AR003 — generic function name, AR006 — no annotations
def process(data):
    return data


# AR003 — generic function name
def handle(x, y):
    return x + y


# AR004 — eval
def run_expression(expr):
    return eval(expr)


# AR004 — importlib.import_module
def dynamic_import(name):
    return importlib.import_module(name)


# AR003 — generic class name
class Manager:
    # AR003 — generic method, AR006 — untyped
    def do_stuff(self, thing):
        return thing


# AR005 — deep inheritance chain (5 levels)
class Base:
    pass


class Entity(Base):
    pass


class Persisted(Entity):
    pass


class Auditable(Persisted):
    pass


class User(Auditable):
    # depth = 4 from User -> Auditable -> Persisted -> Entity -> Base
    pass


# AR004 — __getattr__ dispatch
class DynamicAPI:
    def __getattr__(self, name):
        return lambda **kw: None
