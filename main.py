#!/usr/bin/env python3.13

from automata import Automata, Transition, epsilon


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

    # print(f"{*frozenset({1, 2, 3})}")
