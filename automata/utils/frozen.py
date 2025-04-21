class Frozen(frozenset):
    def __str__(self) -> str:
        return str(set(self))

    def __repr__(self) -> str:
        return str(self)
