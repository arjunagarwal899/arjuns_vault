Show rich output in the terminal using the following: https://rich.readthedocs.io/en/stable/traceback.html

```bash
pip install rich
code PATH_TO_SITE_PACKAGES/sitecustomize.py
```

To that file, add the following:

```python
import lightning
import torch
from rich.traceback import install

install(width=130, code_width=120, word_wrap=True, suppress=(torch, lightning))
```

---

To add to jupyter cell output: 

```bash
ipython profile create
code ~/.ipython/profile_default/ipython_config.py
```

In this file, scroll down to find `c.InteractiveShellApp.exec_lines`, and add the following:

```python
c.InteractiveShellApp.exec_lines = [
    "%load_ext rich",
    "%load_ext autoreload",
    "%autoreload 2",
]
```
