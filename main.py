#!/usr/bin/env python3

from utils.queue import Queue

from typing import TypeVar, Generic
from collections import defaultdict


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


epsilon = Epsilon()

Alphabetic = TypeVar("Alphabetic")
State = TypeVar("State")

Alphabet = set[Alphabetic]
Word = list[Alphabet]
Language = set[Word]


class Transition(Generic[Alphabetic, State]):
    start: Alphabetic
    label: State
    end: Alphabetic

    def __init__(self, start: Alphabetic, label: State, end: Alphabetic) -> None:
        self.start = start
        self.label = label
        self.end = end

    def __str__(self) -> str:
        return f"<{self.start}, {self.label}, {self.end}>"

    def __repr__(self) -> str:
        return str(self)


class Automata(Generic[Alphabetic, State]):
    "Σ"
    sigma: Alphabet
    "Q"
    states: set[State]
    "I"
    initial: set[State]
    "Δ"
    transitions: dict[State, set[Transition[Alphabetic, State]]]
    "F"
    final: set[State]

    def __init__(
        self,
        S: Alphabet,
        Q: set[State],
        I: set[State],
        D: set[Transition[Alphabet, State]],
        F: set[State],
    ) -> None:
        if not I <= Q or not F <= Q:
            raise ValueError("F and I must be subsets of Q")

        self.sigma = S
        self.states = Q
        self.initial = I
        self.transitions = defaultdict(set)
        for transition in D:
            self.transitions[transition.start].add(transition)
        self.final = F

    # returns the states, reachable via the empty label
    def get_c(self, initial: set[State]) -> set[State]:
        traversed: set[State] = set()

        queue = Queue[State](list(initial))
        for state in queue:
            traversed.add(state)
            for transition in self.transitions[state]:
                if transition.label != epsilon:
                    continue
                if transition.end in traversed:
                    continue
                queue.push(transition.end)
        return traversed

    def get_language(self, initial: list[State] = None) -> Language:
        if initial == None:
            initial = self.initial
        language = Language()
        queue = Queue[tuple[State, str]](
            list(map(lambda state: (state, epsilon), initial))
        )
        for state, label in queue:
            if state in self.final:
                language.add(label)
            for transition in self.transitions[state]:
                queue.push((transition.end, label + transition.label))
        return language

    def get_language_with_cycles(self, initial: list[State] = None) -> Language:
        if initial == None:
            initial = self.initial
        language = Language()
        queue = Queue[tuple[State, list[Alphabetic], list[State]]](
            list(map(lambda state: (state, [], []), initial))
        )

        for state, labels, traversed in queue:
            # print(f"<{state}, {labels}, {traversed}>")

            state_occurances = traversed.count(state)

            if state in self.final:
                match state_occurances:
                    case 0:
                        language.add("".join(labels))
                    case 1:
                        cycle_idx = traversed.index(state) + 1
                        before_cycle = "".join(labels[:cycle_idx])
                        cycle = "".join(labels[cycle_idx:])
                        language.add(f"{before_cycle}({cycle})...")

                    case 2:
                        cycle_start = traversed.index(state)
                        cycle_end = traversed[cycle_start + 1 :].index(state)
                        before_cycle = "".join(labels[:cycle_start])
                        cycle = "".join(labels[cycle_start:cycle_end])
                        if cycle == "":
                            continue
                        after_cycle = "".join(labels[cycle_end:])
                        language.add(f"{before_cycle}({cycle})...{after_cycle}")
                pass

            elif state_occurances > 2:
                continue

            for transition in self.transitions[state]:
                # print(transition)
                queue.push(
                    (
                        transition.end,
                        labels + [transition.label],
                        traversed + [state],
                    )
                )
        if "" in language:
            language.remove("")
            language.add(epsilon)
        return language

    def __str__(self) -> str:
        return f"<Σ: {self.sigma}, Q: {self.states}, I: {self.initial}, Δ: {self.transitions}, F: {self.final}>"

    def __repr__(self) -> str:
        return str(self)


if __name__ == "__main__":
    fsm = Automata(
        {"a", "b", epsilon},
        {0, 1, 2, 3, 4},
        {0, 1},
        {
            Transition(0, epsilon, 2),
            Transition(0, "a", 3),
            Transition(1, "a", 2),
            Transition(2, "b", 4),
            Transition(2, epsilon, 4),
            Transition(3, "a", 4),
            Transition(3, "b", 0),
            Transition(4, epsilon, 1),
        },
        {4},
    )
    print(fsm)
    print(fsm.get_c(fsm.initial))
    print(fsm.get_language_with_cycles())
