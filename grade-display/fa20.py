# Fall 2020 Sequence of Actions

import os, roster_export, okpy_export
import gs_export, sections_export, assemble

if not os.path.exists('data'):
    os.makedirs('data')

def update(app):
    print("=================================================")
    roster_export.export(app)

    print("=================================================")
    okpy_export.export(app)

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
