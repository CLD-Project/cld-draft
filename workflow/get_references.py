from pathlib import Path
from sys import argv
import zipfile
import json

def project_path(*paths):
    return Path(__file__).parent.joinpath(*paths)


with open(project_path("references.tsv")) as f:
    references = [[cell.strip() for cell in row.split("\t")] for row in f.readlines()]

with open(project_path("resources.tsv")) as f:
    resources = {line[0]: line for line in [[cell.strip() for cell in
                                             row.split("\t")] for row in
                                            f.readlines()]}

with zipfile.ZipFile(project_path().parent.joinpath("glottolog", "glottolog.json.zip")) as zf:
    with zf.open("glottolog.json") as f:
        data = json.load(f)



try:
    query = argv[1]
except IndexError:
    print("you must provide a glottocode as query")

matching = [ref for ref in references if ref[1] == query]
matching_res = [resources[s] for s in set([ref[2] for ref in matching])]

print("found {0} references matching the language".format(len(matching)))

with open(query + "-references.tsv", "w") as f:
    f.write("\t".join(references[0]) + "\n")
    for row in matching:
        f.write("\t".join(row) + "\n")

with open(query + "-resources.tsv", "w") as f:
    f.write("\t".join(resources["ID"]) + "\n")
    for row in sorted(matching_res):
        f.write("\t".join(row) + "\n")

with open(query + "-sources.bib", "w") as f:
    pass

print("query results have been written to files {0} and {1}".format(
    query + "-resources.tsv",
    query + "-references.tsv")
      )

