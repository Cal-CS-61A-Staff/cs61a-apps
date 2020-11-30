from os import mkdir, walk
from os.path import join, relpath
from subprocess import check_call


class GUIFilter:
    def __init__(self, proj_file):
        self.proj_file = proj_file

    @classmethod
    def include(cls, name):
        ext = name.split(".")[-1]
        return ext in [
            "html",
            "js",
            "gif",
            "css",
            "ttf",
            "ico",
            "py",
            "txt",
            "png",
            "LICENSE",
        ]

    def exclude(self, name):
        if name.split(".")[-1] in ["map", "pyc"]:
            return True
        return name in [
            "Procfile",
            "requirements.txt",
            "asset-manifest.json",
            "runtime.txt",
            "manifest.json",
            "robots.txt",
            "service-worker.js",
            ".git",
            self.proj_file,
        ]

    @staticmethod
    def require_same(name):
        return name in ["dice.py", "ucb.py", "utils.py"]


BUILD_OUTPUT_LOC = "deploy"


def read(path):
    with open(path, "rb") as f:
        return f.read()


def main(proj_file, location):
    filt = GUIFilter(proj_file)

    check_call(["yarn", "build"])
    for dirpath, _, filenames in walk(BUILD_OUTPUT_LOC):
        outdir = join(location, relpath(dirpath, BUILD_OUTPUT_LOC))
        try:
            mkdir(outdir)
        except FileExistsError:
            pass
        for name in filenames:
            inp = join(dirpath, name)
            out = join(outdir, name)
            if filt.exclude(name):
                pass
            elif filt.include(name):
                check_call(["cp", inp, out])
            elif filt.require_same(name):
                with open(inp) as f:
                    inp_c = f.read()
                with open(out) as f:
                    out_c = f.read()
                if inp_c != out_c:
                    raise RuntimeError("{} is different from {}".format(inp, out))
            else:
                raise RuntimeError("unrecognized file: {}".format(inp))


if __name__ == "__main__":
    from sys import argv

    main(*argv[1:])
