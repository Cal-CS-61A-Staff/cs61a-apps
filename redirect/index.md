```{include} README.md
```

## Code Documentation

All of the code for redirection is contained in `main.py`. It tries to retrieve
from a set LOOKUP dictionary and if it doesn't exist tries to directly get a url
from the inst.eecs website. `catch_all()` recieves a path and calls `lookup()`
to get the link. `lookup()` creates the redirect link.

```{eval-rst}
.. automodule:: redirect.main
    :members:
```
