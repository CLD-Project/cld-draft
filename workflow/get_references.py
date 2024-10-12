from pathlib import Path
from sys import argv
import zipfile
import json
import sys

def project_path(*paths):
    return Path(__file__).parent.joinpath(*paths)


with open(project_path("references.tsv")) as f:
    references = [[cell.strip() for cell in row.split("\t")] for row in f.readlines()]

with open(project_path("resources.tsv")) as f:
    resources = {line[0]: line for line in [[cell.strip() for cell in
                                             row.split("\t")] for row in
                                            f.readlines()]}

with zipfile.ZipFile(project_path("glottolog.json.zip")) as zf:
    with zf.open("glottolog.json") as f:
        data = json.load(f)



try:
    query = argv[1]
except IndexError:
    print("you must provide a glottocode as query")
    sys.exit()

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

dups = 0
with open(query + "-sources.bib", "w") as f:
    bibtypes = [
            "author", "year", "editor", "title", "booktitle", "address",
            "publisher", "doi", "pages", "journal", "volume", "number"
            ]
    for row in matching_res:
        source_strings = set(row[6].split(" "))
        text = ""
        if len(source_strings) > 1:
            text += "% <<< Duplicates\n\n"
            dups += 1
        for source in source_strings:
            text += "@" + data["sources"][source]["bibtex_type"] + "{" + row[0] + ",\n"
            for tp in bibtypes:
                entry = data["sources"][source].get(tp)
                if entry:
                    text += "  " + tp + " = {" + entry + "},\n"
            text += "  _glottolog_key = {" + source + "}\n}\n\n"
        if len(source_strings) > 1:
            text += "% Duplicates >>>\n\n"
        f.write(text)


print("query results have been written to files\n\n- {0}\n- {1}\n- {2}".format(
    query + "-resources.tsv",
    query + "-references.tsv",
    query + "-sources.bib")
      )
if dups:
    print('found {0} references with duplicate sources'.format(dups))

