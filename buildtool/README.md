## Overview

This is a `make` alternative with a simpler syntax and some useful features.

## Example
### Hello, World!
To create a buildtool project, place a `WORKSPACE` file at the root of your project. For now, it can be empty. Run `git init` to initialize a git repo in your project root.

Then you can define build rules in `BUILD` files.  Imagine a simple project with one source file: `src/main.c`, that can be compiled with `gcc main.c -c -o ../build/a.out` to produce the output file `build/a.out`. Our project structure looks like:
```
 - WORKSPACE
 - src/
    - main.c
    - BUILD
```
We have placed a `BUILD` file in the `src/` directory. We will declare a rule called `main` that builds `main.c` and produces `a.out` in this `BUILD` file.

```python
# src/BUILD
from buildtool import callback

def impl(ctx):
    ctx.sh("mkdir -p ../build")
    ctx.sh("gcc main.c -c -o ../build/a.out")

callback(
    name="main",
    deps=["main.c"],
    impl=impl,
    out="../build/a.out",
)
```
Let's see what this file does. The `callback` tells `buildtool` that we are declaring a rule with `name="main"`. The `deps` of a rule are the files that the rule requires to run. The `out` is a file (or list of files) that a rule produces from its deps. Finally, the implementation `impl` of a rule describes the actions that a rule performs in order to generate its output from its inputs.

The paths passed into the callback are relative to the folder containing the `BUILD` file.

An `impl` function takes in a single argument: the build context `ctx`. When defining a rule's implementation, do not use functions like `os.system` directly - aside from invoking methods in the `ctx`, all `impl` functions must be side-effect free. Here, `ctx.sh(...)` runs a shell command in the directory containing the `BUILD` folder.

Now we can run this rule. Run `buildtool main` inside the project. The output file `build/a.out` should have appeared.

So far, we haven't done anything that couldn't be done with a simple Makefile. 

However, now try modifying the build rule so `deps=[]`, and rerun `buildtool main` (or just `bt main` for short). We get an error
```
 error: no such file or directory: 'main.c'
```
This is despite the fact that `src/main.c` is clearly still in our repo. Buildtool runs all builds in a separate "sandbox" directory with only the explicitly stated dependencies made available. This means that it is (almost) impossible to make a mistake when specifying rule dependencies, since then the build will fail when run in the sandbox directory.

### Generic Rules
Now imagine that we have a second source file `another.c` in `src/`, and want to compile it to `build/b.out`. One way would be to copy/paste the existing `main` build rule and create a second rule to generate `b.out`. Instead, however, we can define a generic build rule, and _declare_ it twice - once for each of our two targets.

This can be done as follows:
```python
# src/BUILD
from buildtool import callback

def declare(*, name: str, src: str, out: str):
    def impl(ctx):
        ctx.sh("mkdir -p ../build")
        ctx.sh(f"gcc {src} -c -o {out}")
    
    callback(
        name=name,
        deps=[src],
        impl=impl,
        out=out,
    )

declare(name="main", src="main.c", out="../build/a.out")
declare(name="another", src="another.c", out="../build/b.out")
```

The `declare` function is just a standard Python function, and when `src/BUILD` is evaluated, `callback()` is called twice by `declare()` to declare each of our rules.


### Loading Files
In larger repos, it may make sense to move these generic rules into a separate file. Let us do so here, creating a `rules.py` file in the same `src/` directory, so our file hierarchy now looks like:
```
- WORKSPACE
- src/
    - main.c
    - another.c
    - BUILD
    - rules.py
```

We move `declare` into `rules.py`, so
```python
# src/rules.py
from buildtool import callback

def declare(*, name: str, src: str, out: str):
    def impl(ctx):
        ctx.sh("mkdir -p ../build")
        ctx.sh(f"gcc {src} -c -o {out}")
    
    return callback(
        name=name,
        deps=[src],
        impl=impl,
        out=out,
    )
```
To import it from `rules.py`, we can use the `load()` function, as follows:
```python
# src/BUILD
from buildtool import load

rules = load("rules.py")

rules.declare(name="main", src="main.c", out="../build/a.out")
rules.declare(name="another", src="another.c", out="../build/b.out")
```

The path passed to `load()` is relative to the loading file. `*.py` files can also load other `*.py` files, so long as no cycles exist. It is not possible to load a `BUILD` file from another file. Furthermore, it is only possible to declare a rule from a `BUILD` file. Now we can run `bt main` or `bt another` to generate `a.out` and `b.out`, respectively.

### Rule Dependencies
In addition to depending on other files, rules can depend on other rules. Unlike depending on files, depending on other rules will not change the files made available when running builds in the sandbox directory. Instead, if rule `A` depends on rule `B`, then whenever we build rule `A`, rule `B` is guaranteed to also be built.

For instance, we may wish to have a build target to build both `main` and `another` together. This can be done as follows:
```python
# src/BUILD
from buildtool import load, callback

rules = load("rules.py")

rules.declare(name="main", src="main.c", out="../build/a.out")
rules.declare(name="another", src="another.c", out="../build/b.out")

callback(
    name="all",
    deps=[":main", ":another"],
)
```
By adding a `:` in front of the names of a dependency, we signify that it is the name of a rule, not the name of a file. When running builds from the command-line, we can also use this syntax to disambiguate between a rule and a file with the same name (e.g. `bt :all`), but it is not required if the target can be resolved unambiguously.

Now, running `bt all` will build both `a.out` and `b.out`.

If `name` is passed to `callback()`, it will return `:<name>`. This lets us avoid repeating rule names, as follows:
```python
# src/BUILD
from buildtool import load, callback

rules = load("rules.py")

callback(
    name="all",
    deps=[
        rules.declare(name="main", src="main.c", out="../build/a.out"),
        rules.declare(name="another", src="another.c", out="../build/b.out")
    ],
)
```
However, it is good practice to avoid "nesting" rules in this fashion.

### Paths and Globbing
Rather than writing a separate rule for each `.c` file in `src/`, we may wish to automatically declare rules to build them. This can be done using the `find()` function, which lets us glob for files, as follows:
```python
# src/BUILD
from buildtool import load, callback, find
from os.path import basename

rules = load("rules.py")

all_rules = []

for src in find("*.c"):
    name = basename(src)[:-2]
    all_rules.append(rules.declare(name=name, src=src, out=f"../build/{name}.out"))

callback(
    name="all",
    deps=all_rules,
)
```
The path passed to `find()` is relative to the directory containing the `BUILD` file. We can also pass in paths relative to the root of the project, by prefixing them with `//`. So instead of writing `find("*.c")`, we could have equivalently written `find("//src/*.c")`. This syntax for paths relative to the project root can be used elsewhere where paths are required, such as an element of `deps`, the value of `out`, or as an argument to `load()`.

If we run `bt main`, we get the following error:
```
subprocess.CalledProcessError: Command '['gcc //src/main.c -o ../build/main.out']' returned non-zero exit status 1.
```
We see that `find()` has returned a path relative to the project root, which cannot be directly passed to the shell. One fix would be to again use `os.path.basename` in `rules.py` to extract the filename `main.c`. However, this will cause problems if we later try to use our rule to compile a file in a subfolder. Instead, there exists a method `ctx.relative()` that takes in a path of any format and outputs a path relative to the working directory in an implementation.

We can use this method to modify `rules.py` as follows:
```python
# src/rules.py
from buildtool import callback

def declare(*, name: str, src: str, out: str):
    def impl(ctx):
        ctx.sh("mkdir -p ../build")
        ctx.sh(f"gcc {ctx.relative(src)} -c -o {ctx.relative(out)}")
    
    return callback(
        name=name,
        deps=[src],
        impl=impl,
        out=out,
    )
```
For now, we will not worry about updating the `mkdir` call to support subdirectories. Now `bt all` should work correctly.

### Dynamic Dependencies
Sometimes, we do not know all the dependencies of a rule in advance. For instance, imagine that `main.c` depends on `another.c`. If we run `bt main`, we get the error
```
main.c:2:10: fatal error: 'another.c' file not found
```
becaues only explicitly stated dependencies are available when running a build.

One solution would be to update `declare()` to take in a list of dependencies and manually specify that `main.c` depends on `another.c`. Alternatively, we can add a dependency dynamically when running the build.

First, we need to know how to detect dependencies. If we run `gcc main.c -MM`, we obtain:
```shell
$ gcc main.c -MM
main.o: main.c another.c
```
This is in a format acceptable for Makefiles, but we need to process it to extract the raw file names. We can do so by modifying `rules.py` as follows:
```python
# src/rules.py
from buildtool import callback

def declare(*, name: str, src: str, out: str):
    def impl(ctx):
        ctx.sh("mkdir -p ../build")
        raw_deps = ctx.input(sh=f"gcc {ctx.relative(src)} -MM")
        deps = raw_deps.strip().split(" ")[1:]
        ctx.add_deps(deps)
        ctx.sh(f"gcc {ctx.relative(src)} -c -o {ctx.relative(out)}")
    
    return callback(
        name=name,
        impl=impl,
        out=out,
    )
```
First, we use `ctx.input(sh=...)` to run a shell command and read back the stdout. After parsing the output to determine what files to depend on, we then use `ctx.add_deps()` to add them as _dynamic dependencies_, replacing the `deps=[src]` previously passed into `callback()`. Finally, we run the standard compile, as before. Notice that the initial `ctx.input()` call depended on `src`, but it was only added as a dependency _afterwards_. This is allowed with dynamic dependencies, so long as after the `impl()` completes, all the dependencies ever used have been added.

Now, `bt all` successfully builds the target files.

### Workspaces
We now are able to build a simple project. When managing large projects, it is useful to also automate setup of the build environment, so a user can clone the repo, run `buildtool`, and obtain the built output without any manual configuration. This is the role of the `WORKSPACE` file.

In a `WORKSPACE` file, there is a new import available from `buildtool`: the `config`. A simple `WORKSPACE` file may look like this:
```python
# WORKSPACE
from buildtool import config

config.register_default_build_rule(":all")
config.register_output_directory("build")
config.require_buildtool_version("0.1.25")
```

The default build rule is the rule that is invoked when running `bt` in a project directory with no rule specified. The output directory is a directory that is cleaned when running `bt --clean`, in order to remove previous build artifacts (multiple output directories can be registered). Finally, a minimum `buildtool` version can be required, so that if old versions are used to build the project, a clear error message will be printed instructing the user to update.

In addition, we can declare _setup rules_ in the `WORKSPACE` file. Unlike build rules, setup rules are not run in sandboxed directories, so their dependencies are not automatically enforced. While they must specify their outputs, since they run in the main project directory, they are not verified either. Unlike build rules, setup rules cannot use `ctx.add_deps()`,  but must specify their dependencies statically.

For instance, imagine that `gcc` is not present in the `/usr/bin/` directory, but is instead located somewhere else in the `PATH`. The `PATH` is normalized to `/usr/bin/` in build rules, so our previous rule would not work since the shell would not be able to find `gcc`. Instead, we will use a setup rule to detect `gcc` and add a symlink from `//env/bin/gcc` to wherever it is located on the machine. Then we will use this symlink in our build rules to compile our `*.c` files.

We modify our `WORKSPACE` file as follows:
```python
# WORKSPACE
from buildtool import config, callback

def declare_gcc_symlink():
    def impl(ctx):
        target = ctx.input(sh=f"which gcc").strip()
        ctx.sh("mkdir -p env/bin")
        ctx.sh("rm -f env/bin/gcc")
        ctx.sh(f"ln -s {target} env/bin/gcc")
    
    return callback(
        name="gcc",
        impl=impl,
        out="env/bin/gcc",
    )

callback(
    name="init",
    deps=[declare_gcc_symlink()]
)

config.register_default_setup_rule(":init")
config.register_default_build_rule(":all")
config.register_output_directory("build")
config.require_buildtool_version("0.1.25")
```

Notice that the `impl()` of `declare_gcc_symlink()` clears any past outputs before rerunning, since it runs in the project directory directly, not in a sandbox. In addition, notice that we have registered a `default_setup_rule` in our config. If such a rule is registered, buildtool will ensure that it is built before building any subsequent targets.

To run the `gcc` setup rule separately, run `bt setup:gcc`. Unlike build rules, we cannot run `bt env/bin/gcc` to regenerate the file - we can only run setup rules from the command line by their name. Thus, all setup rules are required to have a name, though they can _depend_ on source files or on files built by other setup rules.

Next, we will modify `rules.py` to use `//env/bin/gcc`, instead of `/usr/bin/gcc`. Rather than hardcoding this new path into `ctx.sh`, we will modify the `PATH` used by `ctx.sh()` to look in `//env/bin` and then `/bin`, but not `/usr/bin`. This can be done as follows:
```python
# src/rules.py
from buildtool import callback

ENV = dict(PATH=["@//env/bin/", "/bin"])

def declare(*, name: str, src: str, out: str):
    def impl(ctx):
        ctx.sh("mkdir -p ../build", env=ENV)
        raw_deps = ctx.input(sh=f"gcc {ctx.relative(src)} -MM", env=ENV)
        deps = raw_deps.strip().split(" ")[1:]
        ctx.add_deps(deps)
        ctx.sh(f"gcc {ctx.relative(src)} -c -o {ctx.relative(out)}", env=ENV)

    return callback(
        name=name,
        impl=impl,
        out=out,
    )
```
When we prefix a path with `@//`, it means that the path is relative to the project root directory, even if the build is being run in a sandbox. In contrast, if a path is prefixed with `//`, then it is treated as relative to the sandbox root directory when running a sandboxed builds. Paths can only be prefixed by `@//` in environment variables, not anywhere else.

Notice that we have not defined the `PATH` in `ENV` to be a string, but rather as a list of paths, using buildtool syntax. The buildtool will automatically resolve these paths to absolute paths and concatenate them together to form a string that will be passed into the shell environment. This is done so that absolute paths are never handled directly in build rules - they are to be avoided since they cause issues with caching. If an absolute path is needed as part of a shell command, it can be added to the environment and then accessed using shell syntax.

We can now run `bt all` to regenerate the output. Notice that an `env/` folder has been created, containing the `gcc` symlink. Conventionally, we do not register the `env/` folder (or other targets built by setup rules) as an output directory, since it is unlikely to be the user's intention to clear it when running `bt --clear`.
