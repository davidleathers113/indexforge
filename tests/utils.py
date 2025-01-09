"""Test utilities."""


class ANY:
    """Helper class for type checking in tests."""

    def __init__(self, type_):
        self.type = type_

    def __eq__(self, other):
        return isinstance(other, self.type)

    def __repr__(self):
        return f"ANY({self.type.__name__})"
