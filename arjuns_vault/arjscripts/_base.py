import os


def run_script(scriptname, *args, **kwargs):
    scriptpath = os.path.join(os.path.dirname(__file__), rf"{scriptname}.sh")
    args = " ".join(args)
    kwargs = " ".join([f"--{k} {v}" for k, v in kwargs.items()])
    os.system(f"bash {scriptpath} {args} {kwargs}")
