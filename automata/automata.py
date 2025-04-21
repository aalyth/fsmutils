from __future__ import annotations

import string
import itertools

from typing import TypeVar, Generic

Alphabetic = TypeVar("Alphabetic", bound=str)
State = TypeVar("State")


class Transition(Generic[Alphabetic, State]):
    start: Alphabetic
    label: State
    end: Alphabetic

    def __init__(self, start: Alphabetic, label: State, end: Alphabetic) -> None:
        self.start = start
        self.label = label
        self.end = end

    def __hash__(self):
        return hash((self.start, self.label, self.end))

    def __eq__(self, other):
        if not isinstance(other, Transition):
            return False
        self_tuple = (self.start, self.label, self.end)
        other_tuple = (other.start, other.label, other.end)
        return self_tuple == other_tuple

    def __str__(self) -> str:
        return f"<{self.start}, {self.label}, {self.end}>"

    def __repr__(self) -> str:
        return str(self)


class Automata(Generic[Alphabetic, State]):
    alphabet: set[Alphabetic]
    states: set[State]
    initial_states: set[State]
    transitions: set[Transition]
    delta: dict[State, dict[Alphabetic, set[State]]]
    final_states: set[State]

    def __new__(
        cls,
        alphabet: set[Alphabetic],
        states: set[State],
        initial_states: set[State],
        transitions: set[Transition],
        final_states: set[State],
        *args,
        **kwargs,
    ) -> Automata | DetAutomata:
        if not initial_states.issubset(states):
            raise ValueError("Initial states must be a subset of all states.")
        if not final_states.issubset(states):
            raise ValueError("Final states must be a subset of all states.")

        if initial_states == set() or final_states == set():
            raise ValueError("Initial and final states cannot be empty.")

        deterministic = True
        deterministic_lookup: dict[tuple[State, Alphabetic], State] = {}
        for transition in transitions:
            if transition.start not in states or transition.end not in states:
                raise ValueError(
                    f"Transition from invalid states: {transition.start} -> {transition.end}"
                )
            if transition.label not in alphabet:
                raise ValueError(
                    f"Transition with invalid label: {transition.label} not in {alphabet}"
                )

            if (transition.start, transition.label) in deterministic_lookup:
                deterministic = False
            deterministic_lookup[(transition.start, transition.label)] = transition.end

        if len(initial_states) > 1:
            deterministic = False

        if deterministic:
            return DetAutomata(
                alphabet,
                states,
                transitions,
                initial_states.pop(),
                final_states,
            )

        return Automata(
            alphabet,
            states,
            initial_states,
            transitions,
            final_states,
        )

        def __init__(
            self,
            alphabet: set[Alphabetic],
            states: set[State],
            initial_states: set[State],
            transitions: set[Transition],
            final_states: set[State],
        ):
            self.alphabet = alphabet
            self.states = states
            self.initial_states = initial_states
            self.transitions = transitions
            self.final_states = final_states

            self.delta = {}
            for transition in transitions:
                if transition.start not in self.delta:
                    self.delta[transition.start] = {}
                if transition.label not in self.delta[transition.start]:
                    self.delta[transition.start][transition.label] = set()
                self.delta[transition.start][transition.label].add(transition.end)

        def __or__(self, other: Automata) -> Automata:
            if self.states & other.states:
                raise ValueError("Automata must have unique states for union.")

            start_state = _generate_new_unique_state(self, other)
            new_start_transitions = set()

            def extract_starting_transitions(automata: Automata) -> None:
                for state in automata.initial_states:
                    for letter in automata.delta[state].keys():
                        for end_state in automata.delta[state][letter]:
                            new_start_transitions.add(
                                Transition(start_state, letter, end_state)
                            )

            extract_starting_transitions(self)
            extract_starting_transitions(other)

            return Automata(
                self.alphabet | other.alphabet,
                self.states | other.states | {start_state},
                {start_state},
                self.transitions | other.transitions | new_start_transitions,
                self.final_states | other.final_states,
            )

        def __mul__(self, other: Automata) -> Automata:
            if self.states & other.states:
                raise ValueError("Automata must have unique states for concatenation.")

            transitions = set()
            for state in self.final_states:
                for starting_state in other.initial_states:
                    for letter in other.delta[starting_state].keys():
                        for end_state in other.delta[starting_state][letter]:
                            transitions.add(Transition(state, letter, end_state))

            final_states = other.final_states
            if other.initial_states & self.final_states:
                final_states |= self.final_states

            return Automata(
                self.alphabet | other.alphabet,
                self.states | other.states,
                self.initial_states,
                self.transitions | other.transitions | transitions,
                final_states,
            )

        def _generate_new_unique_state(self, other: "Automata" | None = None) -> State:
            other_states: set[State] = set()
            if other is not None:
                other_states = other.states

            lookup_states = self.states | other_states
            for letter in string.ascii_lowercase:
                if letter not in lookup_states:
                    return letter

            for i in itertools.count(start=1):
                if str(i) not in lookup_states:
                    return str(i)

            assert False, "unrachable code"


class DetAutomata(Automata[Alphabetic, State]):
    initial_state: State
    delta: dict[State, dict[Alphabetic, State]]

    def __init__(
        self,
        alphabet: set[Alphabetic],
        states: set[State],
        transitions: set[Transition],
        initial_state: State,
        final_states: set[State],
    ):
        self.states = states
        self.alphabet = alphabet
        self.transitions = transitions
        self.initial_state = initial_state
        self.final_states = final_states

    def __repr__(self):
        return f"DetAutomata(states={self.states}, alphabet={self.alphabet}, transitions={self.transitions}, initial_state={self.initial_state}, final_states={self.final_states})"
