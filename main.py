#!/usr/bin/env python3

from utils.queue import Queue

from typing import TypeVar, Generic
from collections import defaultdict
from itertools import product as cartesian


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
    # transitions: dict[State, set[Transition[Alphabetic, State]]]
    transitions: dict[State, dict[Alphabetic, set[State]]]
    _raw_delta: set[Transition[Alphabetic, State]]
    "F"
    final: set[State]

    _deterministic: bool
    _total: bool

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

        self._raw_delta = D
        self.transitions = defaultdict(lambda: defaultdict(set))
        for transition in D:
            self.transitions[transition.start][transition.label].add(transition.end)
            if len(self.transitions[transition.start][transition.label]) > 1:
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

    def as_table(self) -> str:
        def _str(val) -> str:
            if type(val) is frozenset:
                return str(set(val))
            return str(val)

        # the maximum number of characters, that has been encountered for the
        # given column, determening the width of the whole column
        default_widths: dict[Alphabetic, int] = {char: 1 for char in self.alphabet}
        for state in self.states:
            for char in self.alphabet:
                current_width = len(_str(self.transitions[state][char]))
                if current_width > default_widths[char]:
                    default_widths[char] = current_width

        # in order to keep the ordering
        ordered_alphabet = list(self.alphabet)
        ordered_states = list(self.states)

        # +4 for the `-> *` possible combination and +2 for the whitespaces
        MAX_CHAR_WIDTH = max(map(lambda x: len(_str(x)), self.states)) + 4 + 2
        top_row = f"{'Δ': ^{MAX_CHAR_WIDTH}}"

        border_row = "-" * MAX_CHAR_WIDTH

        for char in ordered_alphabet:
            char_width = default_widths[char]
            top_row += f"|{_str(char): ^{char_width}}"
            border_row += f"+{'-' * char_width}"

        result = top_row
        for state in ordered_states:
            final = "*" if state in self.final else ""
            initial = "-> " if state in self.initial else ""

            tmp = f"{initial}{final}{_str(state)} "
            row = f"{tmp: >{MAX_CHAR_WIDTH}}"

            for char in ordered_alphabet:
                char_entry = "-"
                neighbouring_states = self.transitions[state][char]
                if len(neighbouring_states) > 0:
                    char_entry = ",".join(map(_str, neighbouring_states))
                row += f"|{char_entry: ^{default_widths[char]}}"
            result += f"\n{border_row}\n{row}"

        return result + "\n"

    # Automata union
    def __or__(self, other: "Automata") -> "Automata":
        if self.states & other.states != set():
            raise ValueError("uniting automatas mustn't have intersecting states")
        states = self.states | other.states
        start_state = self.__generate_new_state(states)

        # the `start_state` should be final only if a starting state is a final
        # in the source FSMs
        final_state = set()
        if self.initial & self.final != set() or other.initial & other.final != set():
            final_state = {start_state}

        transitions = self._raw_delta | other._raw_delta
        start_states = self.initial | other.initial
        for state in start_states:
            neighbours = list(self.transitions[state].items())
            neighbours.extend(other.transitions[state].items())
            delta = [(label, end) for label, bucket in neighbours for end in bucket]
            for label, end in delta:
                transitions.add(Transition(start_state, label, end))

        return Automata(
            self.alphabet | other.alphabet,
            states | {start_state},
            {start_state},
            transitions,
            self.final | other.final | final_state,
        )

    # Automata concatenation
    def __mul__(self, other: "Automata") -> "Automata":
        if self.states & other.states != set():
            raise ValueError("uniting automatas mustn't have intersecting states")

        final_states = other.final
        if other.initial & other.final != set():
            final_states |= self.final

        # transitions = self.__unite_transitions(other)
        transitions = self._raw_delta | other._raw_delta
        for final in self.final:
            for start in other.initial:
                for label, bucket in other.transitions[start].items():
                    for end_state in bucket:
                        transitions.add(Transition(final, label, end_state))

        return Automata(
            self.alphabet | other.alphabet,
            self.states | other.states,
            self.initial,
            transitions,
            other.final,
        )

    def kleene_star(self) -> "Automata":
        start_state = self.__generate_new_state()

        # transitions = set.union(*self.transitions.values())
        transitions = self._raw_delta
        for start in self.initial:
            for label, bucket in self.transitions[start].items():
                for end_state in bucket:
                    transitions.add(Transition(start_state, label, end_state))

        return Automata(
            self.alphabet,
            self.states | {start_state},
            {start_state},
            transitions,
            self.final | {start_state},
        )

    def __and__(self, other: "Automata") -> "Automata":
        start_states = set(cartesian(self.initial, other.initial))
        transitions = set()
        traversed: set[(State, State)] = set()

        states_queue = Queue(list(start_states))
        for lstate, rstate in states_queue:
            if (lstate, rstate) in traversed:
                continue
            traversed.add((lstate, rstate))

            for label in self.alphabet:
                combined_end_states = set(
                    cartesian(
                        self.transitions[lstate][label],
                        other.transitions[rstate][label],
                    )
                )

                for end_state in combined_end_states:
                    transitions.add(Transition((lstate, rstate), label, end_state))

                    if end_state not in traversed:
                        states_queue.push(end_state)

        final_states = {
            (lstate, rstate)
            for lstate, rstate in traversed
            if lstate in self.final and rstate in other.final
        }

        return Automata(
            self.alphabet, traversed, start_states, transitions, final_states
        )

    # Convert automata to deterministic
    def deterministic(self) -> "Automata":
        if self._deterministic:
            return self

        epsilon_lookup = {state: self.get_c_epsilon({state}) for state in self.states}

        transitions = set()
        traversed: set[set[State]] = set()
        initial_state = set.union(*[epsilon_lookup[state] for state in self.initial])
        states_queue = Queue([initial_state])
        alphabet = self.alphabet - {epsilon}
        for state_set in states_queue:
            # the state must be frozen, so it can be hashed and indexed
            frozen_state = frozenset(state_set)
            if frozen_state in traversed:
                continue
            traversed.add(frozen_state)

            for label in alphabet:
                epsilon_neigh = [
                    epsilon_lookup[s]
                    for state in state_set
                    for s in self.transitions[state][label]
                ]
                if epsilon_neigh == []:
                    continue
                neighbour = set.union(*epsilon_neigh)
                transitions.add(
                    Transition(frozenset(state_set), label, frozenset(neighbour))
                )

                if neighbour not in traversed:
                    states_queue.push(neighbour)

        final_states = {
            state for state in traversed if self.final.intersection(state_set) != set()
        }
        return Automata(
            alphabet,
            traversed,
            {frozenset(initial_state)},
            transitions,
            final_states,
        )

    # returns the states, reachable via the empty label
    def get_c_epsilon(self, initial: set[State]) -> set[State]:
        traversed: set[State] = set()

        queue = Queue(list(initial))
        for state in queue:
            traversed.add(state)
            for neighbour in self.transitions[state][epsilon]:
                if neighbour in traversed:
                    continue
                traversed.add(neighbour)
                queue.push(neighbour)
        return traversed

    def __str__(self) -> str:
        return f"<Σ: {self.alphabet}, Q: {self.states}, I: {self.initial}, Δ: {self.transitions}, F: {self.final}>"

    def __repr__(self) -> str:
        return str(self)

    def __generate_new_state(self, states: set[State] = None) -> str:
        if type(states) != "set":
            states = self.states
        state = 1
        while True:
            if state not in states:
                break
            state += 1
        return state


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

    ex_2_A = Automata.from_table(
        {"s"},
        {"p", "q"},
        {
            Transition("s", 0, "s"),
            Transition("s", 1, "p"),
            Transition("p", 0, "q"),
            Transition("q", 1, "p"),
        },
    )
    ex_2_B = Automata.from_table(
        {"r"},
        {"t"},
        {
            Transition("r", 0, "r"),
            Transition("r", 1, "r"),
            Transition("r", 1, "t"),
        },
    )
    print((ex_2_A * ex_2_B).as_table())

    ex_3_A = Automata.from_table(
        {"p"},
        {"r"},
        {
            Transition("p", "b", "r"),
            Transition("q", "a", "p"),
            Transition("q", "a", "q"),
            Transition("q", "b", "r"),
            Transition("r", "a", "p"),
            Transition("r", "b", "p"),
        },
    )
    print(ex_3_A.kleene_star().as_table())

    ex_4_A = Automata.from_table(
        {"s"},
        {"s"},
        {
            Transition("s", "a", "s"),
            Transition("s", "b", "s"),
            Transition("s", "b", "p"),
            Transition("p", "a", "p"),
        },
    )
    ex_4_B = Automata.from_table(
        {"q"},
        {"r"},
        {
            Transition("q", "a", "q"),
            Transition("q", "b", "r"),
            Transition("r", "a", "q"),
            Transition("r", "a", "r"),
            Transition("r", "b", "t"),
            Transition("t", "a", "q"),
        },
    )
    print((ex_4_A & ex_4_B).as_table())

    ex_5_A = Automata.from_table(
        {0},
        {2, 3},
        {
            Transition(0, "a", 1),
            Transition(1, epsilon, 2),
            Transition(2, "a", 3),
            Transition(2, "a", 4),
            Transition(2, "b", 3),
            Transition(3, epsilon, 2),
            Transition(3, epsilon, 0),
            Transition(4, "a", 1),
            Transition(4, "b", 1),
            Transition(4, "b", 2),
            Transition(4, epsilon, 3),
        },
    )
    print(ex_5_A.deterministic().as_table())
