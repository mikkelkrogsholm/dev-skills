"""Exercises AR006 coverage for all Python argument kinds.
Every public function here is expected to trigger AR006."""


def positional_only(x, /, y, *, z):
    return x + y + z


def with_varargs(*args, **kwargs):
    return args, kwargs


def returns_but_untyped_param(x) -> int:
    return x


def typed_but_no_return(x: int):
    return x


class Billing:
    def __init__(self, client):  # missing type on 'client'; __init__ return not required
        self.client = client

    def charge(self, amount):
        return amount
