#!/usr/bin/env python3
"""Playful "name numerology" and letter stats for a name.

Usage:
    python name_facts.py "Ada Lovelace"
"""

import sys

VOWELS = set("aeiou")
# Pythagorean numerology: a=1, b=2, ... i=9, j=1, ...
LETTER_VALUES = {c: (i % 9) + 1 for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")}


def digit_root(n: int) -> int:
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def facts(name: str) -> str:
    s = name.strip()
    letters = [c for c in s if c.isalpha()]
    lower = [c.lower() for c in letters]
    vowels = [c for c in lower if c in VOWELS]
    consonants = [c for c in lower if c not in VOWELS]
    words = [w for w in s.split() if w]
    initials = "".join(w[0].upper() for w in words)
    total = sum(LETTER_VALUES.get(c, 0) for c in lower)

    return "\n".join(
        [
            f'Name: "{s}"',
            f"Letters: {len(letters)}  |  Vowels: {len(vowels)}  |  Consonants: {len(consonants)}",
            f"Unique letters: {len(set(lower))}",
            f"Initials: {initials or '-'}",
            f"Reversed: {s[::-1]}",
            f"Numerology sum: {total}  ->  destiny number: {digit_root(total) if total else 0}",
        ]
    )


def main() -> None:
    args = sys.argv[1:]
    name = " ".join(args) if args else ""
    if not name.strip():
        print("No name provided.")
        sys.exit(1)
    print(facts(name))


if __name__ == "__main__":
    main()
