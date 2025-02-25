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

    def __hash__(self) -> int:
        return 0


epsilon = Epsilon()

# Although a TypeVar(), this technically is just a `char`, but there exists no
# such type, so a custom annotation is used and not the default `str`.
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
    alphabet: Alphabet
    "Q"
    states: set[State]
    "I"
    initial: set[State]
    "Δ"
    transitions: dict[State, set[Transition[Alphabetic, State]]]
    "F"
    final: set[State]

    _deterministic: bool

    def __init__(
        self,
        S: Alphabet,
        Q: set[State],
        I: set[State],
        D: set[Transition[Alphabetic, State]],
        F: set[State],
    ) -> None:
        if not I <= Q or not F <= Q:
            print(f"F: {F}")
            print(f"I: {I}")
            print(f"Q: {Q}")
            raise ValueError("F and I must be subsets of Q")

        self._deterministic = True
        self.alphabet = S
        self.states = Q
        self.initial = I
        self.final = F

        self.transitions = defaultdict(set)
        for transition in D:
            transition_bucket = self.transitions[transition.start]
            transition_bucket.add(transition)
            if len(transition_bucket) > 1:
                self._deterministic = False

    def from_table(
        initial: set[State],
        final: set[State],
        transitions: set[Transition[Alphabetic, State]],
    ) -> "Automata":
        alphabet = set()
        states = set()

        for t in transitions:
            states.add(t.start)
            states.add(t.end)
            alphabet.add(t.label)

        return Automata(alphabet, states, initial, transitions, final)

    # returns the states, reachable via the empty label
    def get_c_epsilon(self, initial: set[State]) -> set[State]:
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

    # NOTE: works only for languages without cycles
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

    # NOTE: does not work for languages with cycles
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

    def as_table(self) -> str:
        lookup: dict[State, dict[Alphabetic, list[State]]] = defaultdict(
            lambda: defaultdict(list)
        )

        for transitions_bucket in self.transitions.values():
            for t in transitions_bucket:
                lookup[t.start][t.label].append(t.end)

        # the maximum number of characters, that has been encountered for the
        # given column, determening the width of the whole column
        default_widths: dict[Alphabetic, int] = {char: 1 for char in self.alphabet}
        for transitions_bucket in lookup.values():
            for char in self.alphabet:
                if len(transitions_bucket[char]) > default_widths[char]:
                    default_widths[char] = len(transitions_bucket[char])

        # in order to keep the ordering
        ordered_alphabet = sorted(list(self.alphabet))
        ordered_states = sorted(list(self.states))

        # the widest posible char is ` -> *c `, which holds in exactly 7 chars
        MAX_CHAR_WIDTH = 7
        top_row = f"{'Δ': ^{MAX_CHAR_WIDTH}}"

        border_row = "-" * MAX_CHAR_WIDTH

        # (width-1) is for the "," separator and the +2 is for surrounding spaces
        width_formula = lambda width: width + (width - 1) + 2
        default_widths = {
            state: width_formula(width) for state, width in default_widths.items()
        }

        for char in ordered_alphabet:
            char_width = default_widths[char]
            top_row += f"|{str(char): ^{char_width}}"
            border_row += f"+{'-' * char_width}"

        result = top_row
        for state in ordered_states:
            final = "*" if state in self.final else ""
            initial = "-> " if state in self.initial else ""

            tmp = f"{initial}{final}{state} "
            row = f"{tmp: >{MAX_CHAR_WIDTH}}"

            for char in ordered_alphabet:
                char_entry = "-"
                neighbouring_states = lookup[state][char]
                if len(neighbouring_states) > 0:
                    char_entry = ",".join(map(str, neighbouring_states))
                row += f"|{char_entry: ^{default_widths[char]}}"
            result += f"\n{border_row}\n{row}"

        return result + "\n"

    def __or__(self, other: "Automata") -> "Automata":
        if self.states & other.states != set():
            raise ValueError("")
        states = self.states | other.states
        start_state = 1
        while True:
            if str(start_state) not in states:
                break
            start_state += 1
        start_state = str(start_state)

        # the `start_state` should be final only if a starting state is a final
        # in the source FSMs
        final_state = set()
        if self.initial & self.final != set() or other.initial & other.final != set():
            final_state = {start_state}

        transitions = set.union(*self.transitions.values()) | set.union(
            *other.transitions.values()
        )
        start_states = self.initial | other.initial
        for state in start_states:
            for t in self.transitions[state]:
                transitions.add(Transition(start_state, t.label, t.end))
            for t in other.transitions[state]:
                transitions.add(Transition(start_state, t.label, t.end))

        return Automata(
            self.alphabet | other.alphabet,
            states | {start_state},
            {start_state},
            transitions,
            self.final | other.final | final_state,
        )

    def __mul__(self, other: "Automata") -> "Automata":
        pass

    # this actually corresponds to the unary `*` operator similar to
    # dereferencing the object
    def __iter__(self) -> "Automata":
        pass

    def deterministic(self) -> "Automata":
        pass

    def __str__(self) -> str:
        return f"<Σ: {self.alphabet}, Q: {self.states}, I: {self.initial}, Δ: {self.transitions}, F: {self.final}>"

    def __repr__(self) -> str:
        return str(self)


if __name__ == "__main__":
    fsm = Automata.from_table(
        {0, 1},
        {4},
        {
            Transition(0, epsilon, 2),
            Transition(0, "a", 3),
            Transition(1, "a", 2),
            Transition(1, "a", 4),
            Transition(2, "b", 4),
            Transition(2, epsilon, 4),
            Transition(3, "a", 4),
            Transition(3, "b", 0),
            Transition(4, epsilon, 1),
        },
    )
    # print(fsm)
    # print(fsm.get_c_epsilon(fsm.initial))
    # print(fsm.get_language_with_cycles())
    # print(fsm.as_table())

    ex_1_A = Automata.from_table(
        {"s"},
        {"q"},
        {
            Transition("s", "a", "s"),
            Transition("s", "a", "p"),
            Transition("p", "a", "p"),
            Transition("p", "a", "q"),
            Transition("p", "b", "s"),
            Transition("q", "b", "p"),
        },
    )

    ex_1_B = Automata.from_table(
        {"t"},
        {"t"},
        {
            Transition("r", "a", "r"),
            Transition("r", "b", "t"),
            Transition("t", "a", "r"),
            Transition("t", "a", "t"),
        },
    )

    print((ex_1_A | ex_1_B).as_table())
