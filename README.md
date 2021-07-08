### Library and Worksheets for gravitationalballoon.blogspot.com

This material is for the blog at:

https://gravitationalballoon.blogspot.com

It is basically "rebooted" material, because the original work was done in
Excel using macros. The original macros are in the `ported/` folder.
Some have been converted into a python library.

#### Python library

To run anything, you need a checkout of this repo. Get started:

```
pip install -r requirements.txt
pip install -e .
```

This will make the `gb` module importable.

The pytest tests should run with `py.test tests/`.

#### Notebooks

Juypter notebooks are in the `content/` folder and this is where any
human-readable work will go. If you're not familiar...

```
jupyter notebook
```

Will boot it up in the browser.
