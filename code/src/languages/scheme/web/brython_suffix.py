# noinspection PyUnreachableCode

import browser

if False:
    from IGNORE_needed import *

# brython nonsense!
_launchtext = """CS61A Scheme Web Interpreter
--------------------------------------------------------------------------------
Welcome to the 61A Scheme web interpreter! 
The source for this interpreter is restricted, but you'll build it yourself as your Scheme Project!

To visualize a list, call (draw <list>).
To draw list visualizations automatically, call (autodraw).
To view an environment diagram of your entire program, call (visualize).
To launch an editor associated with your console, call (editor).
To run a doctest, call (expect <expr> <output>).
"""


class Stream:
    def __init__(self, obj):
        self.obj = obj

    def write(self, raw):
        self.obj.write(raw)


def write(data):
    stdout.write(str(data))


def err(data):
    stderr.write(str(data))


def exit(data):
    browser.self.exit.write(data)


def _tscheme_prep():
    if turtle is None:
        init_turtle()


def init_turtle():
    global turtle

    sys.path.insert(0, sys.path[0] + "/static/python/overrides")
    # noinspection PyUnresolvedReferences
    import abstract_turtle.turtle as t

    sys.path[:] = sys.path[1:]

    turtle = sys.modules["turtle"] = t

    # noinspection PyUnresolvedReferences
    from abstract_turtle import LoggingCanvas

    class JSONCanvas(LoggingCanvas):
        def on_action(self, log_line):
            print("TURTLE: " + json_repr(log_line), end="")

    turtle.set_canvas(JSONCanvas(1000, 1000))
    turtle.mode("logo")


sys.stdout.write = write
sys.stderr.write = err
sys.stdout.__len__ = sys.stderr.__len__ = lambda: 0

stdout = Stream(browser.self.stdout)
stderr = Stream(browser.self.stderr)

src = ""
firstLine = True


def record_exec(code, wrap):
    if wrap:
        out = "(ignore-error\n"
        for line in code.split("\n"):
            out += "             " + line + "\n"
        out += ")\n"
        record_exec(out, False)
    else:
        print("EXEC: " + code, end="")


frame = create_global_frame()

DEBUG_HOOK = "DEBUG: "


def handle_input(line):
    global src, firstLine
    if firstLine:
        debugging = line.startswith(DEBUG_HOOK)
        if debugging:
            line = line[len(DEBUG_HOOK) :]
        callback = (lambda x: debug_eval(x, frame)) if debugging else run_expr
        firstLine = False
        if not line:
            print(_launchtext)
        try:
            buff = Buffer(tokenize_lines(line.split("\n")))
            while buff.current():
                callback(scheme_read(buff))
        except Exception as e:
            err("ParseError: " + str(e) + "\n")
        if debugging:
            err("scm> ")
            exit("")
        else:
            err("scm> ")
    else:
        src += line
        try:
            buff = Buffer(tokenize_lines(src.split("\n")))
            while buff.more_on_line:
                run_expr(scheme_read(buff))
        except Exception as e:
            if isinstance(e, EOFError) or "unexpected end" in repr(e):
                err("...> ")
                return
            err("ParseError: " + str(e) + "\n")
        src = ""
        err("scm> ")


def run_expr(expr):
    try:
        ret = scheme_eval(expr, frame)
        if ret is not None:
            print(repl_str(ret))
        record_exec(str(expr), False)
        if isinstance(ret, Pair) and autodraw_active:
            draw(ret)
    except Exception as e:
        handle_error(frame)
        record_exec(str(expr), True)
        if isinstance(e, RuntimeError):
            err("Error: maximum recursion depth exceeded" + "\n")
        else:
            err("Error: " + str(e) + "\n")


browser.self.stdin.on(handle_input)
