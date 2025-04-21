class Epsilon(str):
    def __add__(self, other: any) -> any:
        return other

    def __radd__(self, other: any) -> any:
        return other

    def __mul__(self, other: int) -> list["Epsilon"]:
        return [self] * other

    def __rmul__(self, other: int) -> list["Epsilon"]:
        return self * other

    def __str__(self) -> str:
        return "ε"

    def __repr__(self) -> str:
        return str(self)

    def __hash__(self) -> int:
        return 0
