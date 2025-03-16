import os
from pprint import pprint


def print_notes(filename):
    if not os.path.exists(rf"./{filename}.txt"):
        raise ValueError(f"File {filename}.txt not found")

    with open(rf"./{filename}.txt") as file:
        pprint(file.read())
