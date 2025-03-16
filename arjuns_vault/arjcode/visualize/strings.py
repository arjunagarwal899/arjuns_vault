def get_maxlen(arr):
    """
    Utility function. Returns the length of the element having the maximum length in a list

    Args:
        arr (list): the list of strings

    Returns:
        int: the maximum length
    """
    if not isinstance(arr, list):
        try:
            arr = list(arr)
        except Exception:
            return -1

    if not arr:
        return 0

    return len(max(arr, key=len))


def show_keys_hierarchy(mydict, prefix="", show_values=False):
    """
    List all the keys in a nested dictionary of unspecified depth in a readable manner

    Args:
        mydict (dict): The dict to be visualized
        prefix (str, optional): Any prefix to be added to each element. Defaults to "".
        show_values (bool, optional): Will show the deepest values instead of the datatype if set to True.
    """

    if not isinstance(mydict, dict):
        return

    maxlen = get_maxlen(mydict.keys()) + 1

    for key, value in mydict.items():
        print(f"{prefix}{key.ljust(maxlen)}: ", end="")
        if show_values and not isinstance(value, dict) and len(str(value)) < 250:
            print(value)
        else:
            print(type(value))
        show_keys_hierarchy(value, f"{prefix}\t", show_values)
