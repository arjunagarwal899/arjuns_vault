import os


def print_notes(filename):
    filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), rf"{filename}.txt"))
    if not os.path.exists(filepath):
        raise ValueError(f"File {filepath} not found")

    with open(filepath) as file:
        print(file.read())
