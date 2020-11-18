# Fall 2020 Sequence of Actions

import argparse, sys, okpy_export
import gs_export, sections_export, assemble

import os
if not os.path.exists('data'):
    os.makedirs('data')

def update():
    print("=================================================")
    okpy_export.export()

    print("=================================================")
    gs_export.export("mt1")

    print("=================================================")
    gs_export.export("mt2")

    print("=================================================")
    sections_export.export()

    print("=================================================")
    assemble.assemble()

    print("=================================================")

if __name__ == '__main__':
    update()
