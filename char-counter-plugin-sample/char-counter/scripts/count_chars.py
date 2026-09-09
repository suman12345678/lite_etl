#!/usr/bin/env python3
"""Count the number of characters in a name.

Usage:
    python count_chars.py "Ada Lovelace"      # name from command-line args
    python count_chars.py                      # will prompt for input
"""

import sys


def count_chars(name: str) -> dict:
    stripped = name.strip()
    return {
        "name": stripped,
        "total": len(stripped),
        "no_spaces": len(stripped.replace(" ", "")),
        "letters": sum(c.isalpha() for c in stripped),
    }


def main() -> None:
    args = sys.argv[1:]
    if args:
        name = " ".join(args)
    else:
        try:
            name = input("Enter a name: ")
        except EOFError:
            print("No name provided.")
            sys.exit(1)

    if not name.strip():
        print("No name provided.")
        sys.exit(1)

    result = count_chars(name)
    print(f'Name: "{result["name"]}"')
    print(f"Characters (including spaces): {result['total']}")
    print(f"Characters (excluding spaces): {result['no_spaces']}")
    print(f"Letters only:                  {result['letters']}")


if __name__ == "__main__":
    main()
