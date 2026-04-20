"""Exercises suppression pragmas — linter should report zero findings here
because every would-be finding is suppressed."""


class OrderManager:  # agent-lint: disable=AR003
    pass


def process(data):  # agent-lint: disable=AR003,AR006
    return data


# file-level escape hatch for AR004 in this module
# agent-lint: disable-file=AR004


def use_eval(s):  # agent-lint: disable=AR006
    return eval(s)
