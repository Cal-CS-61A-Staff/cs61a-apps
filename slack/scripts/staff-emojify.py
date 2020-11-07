import shutil, sys
from os import listdir, path
from collections import Counter

""" Takes in 2 arguments: an input directory staff images with filename format 
firstname-lastname and an output directory. Returns a duplicate of all staff 
images with filename in format firstname or firstname-lastinitial if multiple
staff members have the same firstname. Also returns mapping.txt in the output
folder, which lists the mapping between names and image titles."""


supported_types = (".png", ".jpg", ".jpeg", ".tiff")
images = []
for f in listdir(sys.argv[1]):
    if f.lower().endswith(supported_types):
        images.append(f)
    else:
        print("ignored " + f)

seen = set()
overlap = [
    k for k, v in Counter(map(lambda i: i.split("-")[0], images)).items() if v > 1
]

mapping = ""
for image in images:
    split = image.split(".")
    names, extension = split[0].split("-"), split[1]
    extension, splitname = image.split(".")[1], image.split(".")
    if image.split("-")[0] in overlap:
        mapping += f"{' '.join(names)} \t {names[0] + '-' + names[1][:1]}\n"
        filename = path.join(
            sys.argv[2], names[0] + "-" + names[1][:1] + "." + extension
        )
    else:
        mapping += f"{' '.join(names)} \t {names[0]}\n"
        filename = path.join(sys.argv[2], names[0] + "." + extension)
    shutil.copyfile(path.join(sys.argv[1], image), filename)

print(mapping)
with open(path.join(sys.argv[2], "mapping.txt"), "w") as lst:
    lst.write(mapping)
