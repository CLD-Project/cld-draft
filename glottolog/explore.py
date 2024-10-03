import collections
import re
from pyglottolog import Glottolog
from pyglottolog.references.bibfiles import Entry
from tqdm import tqdm as progressbar
from zipfile import ZipFile
from pathlib import Path
from cldfcatalog import Config

preprocess_authors = {
        "Hall and A., Robert and Jr.": "Hall Junior, Robert A.",
        "Joyce Huckett and Awadoudo and Huckett Adiguma and Awadoudo Joyce and Adiguma and Laumamala": \
                "Huckett, Joyce and Navakwaya, Fuwali and Awadoudo, Adilo'a",

        }

unify_authors = {
        "others": None,
        "trans.": None,
        "____": None,
        "____ ____": None,
        "No Author Stated": "Anonymous, Unknown Author",
        "Anonymous": "Anonymous, Unknown Author",
        "[Anonymous]": "Anonymous, Unknown Author",
        "Unknown Author": "Anymous, Unknown Author",
        "trans. trans.": None,
        "trans. ___": None,
        "___, trans.": None,
        "___ ___": None,
        "___, ___": None,
        "trans. Author Unknown": None,
        "Unknown, trans. Author": None,
        "others trans.": None,
        "trans. others": None,
        "trans., others": None,
        "others, trans.": None,
        "[s.n]": None,
        "Instituto Lingüístico de Verano": "SIL, Summer Institute of Linguistics",
        "[UK]": None,
        "Anónimo": "Anonymous, Unknown Author",
        "CEDI": "CEDI, CEDI",
        "Anonymous, {}": "Anonymous, Unknown Author",
        "Wangka Maya Pilbara Aboriginal Language Center": "WMPALC, Wangka Maya Pilbara Aboriginal Language Center",
        "[SIL]": "SIL, Summer Institute of Linguistics",
        "[Ghana]": None,
        "[South_Africa]": None,
        "N/A": "Anonymous, Unknown Author",
        "Jochelson, Waldemar [Iokhel'son, Vladimir]": "Jochelson, Waldemar",
        "Jr.": None,
        "[SWA/Namibia]": None,
        "No Author Stated,": "Anonymous, Unknown Author",
        "{No Author Stated": "Anonymous, Unknown Author",
        "comps.": None,
        "[1???]": None,
        "[White_Fathers]": None,
        "Deibler, Jr., Ellis W.": "Deibler Junior, Ellis W.",
        "Salser, Jr., Jay K.": "Salser Junior, Jay K.",
        "Jones, Jr., Robert B.": "Jones Junior, Robert B.",
        "CIDCA": "CIDCA, CIDCA",
        "China": None,
        "___": None,
        "ISO 639-3 Registration Authority": "ISO 639, ISO 639-3 Registration Authority",
        "SIL": "SIL, Summer Institute of Linguistics",
        "SIL International": "SIL, Summer Institute of Linguistics",
        "SIL Ethiopia": "SIL, Summer Institute of Linguistics",
        "Benishangul-Gumuz Language Development Project": "BGLDP, Benishangul-Gumuz Language Development Project",
        "SIL Cameroun": "SIL, Summer Institute of Linguistics",
        "SIL Indonesia": "SIL, Summer Institute of Linguistics",
        "Starosts. S.": "Starostin, Sergey A.",
        "INEI": "INEI, INEI",
        }

def author_string(author):
    """
    Function unifies the author string of BibTeX entries.

    :returns: List of authors normalized by [(family_name, first_name)].
    """
    author = preprocess_authors.get(author, author)
    if " AND " in author:
        author = author.replace(" AND ", " and ")
    persons = [unify_authors.get(a, a) for a in author.split(" and ")]
    out = []
    for person in persons:
        if not person:
            continue
        if "," in person:
            try:
                last, first = person.split(", ")
            except:
                last = person
                first = "?"
        else:
            try:
                tmp = person.split(" ")
                first = " ".join(tmp[:-1])
                last = tmp[-1]
            except:
                last = person
                first = "?"
        out += [(last, first)]
    return out


cfg = Config.from_file()
g_ = Glottolog(cfg.get_clone("glottolog"))
glottocodes = g_.languoids_by_code()

print("[i] loaded Glottolog data")

if not Path("glottolog-5.0.bib").exists():
    with ZipFile("glottolog-5.0.bib.zip") as zf:
        with zf.open("glottolog-5.0.bib") as f:
            lines = [row.decode("utf-8") for row in f]
    print("[i] loaded bibliography from zip-file")
else:
    with open("glottolog-5.0.bib") as f:
        lines = [row for row in f]
    print("[i] loaded bibliography from BibTeX-file")

data = collections.defaultdict(dict)
cols = collections.defaultdict(list)

for row in progressbar(lines, desc="parsing bibtex"):
    if row.startswith("@"):
        key = row.split("{")[1].strip()[:-1]
    if row.startswith("   ") and " = {" in row:
        parts = row.strip().split(" = {")
        attr, val = parts[0], " = {".join(parts[1:])
        data[key][attr] = val.strip("},")
    if "lgcode = " in row:
        codes = row.strip().split(" = {")[1][:-2]
        ncodes = Entry.lgcodes(codes)
        for ncode in ncodes:
            if ncode in glottocodes:
                if glottocodes[ncode].category == "Spoken L1 Language" and \
                        glottocodes[ncode].macroareas:
                    cols[glottocodes[ncode].glottocode] += [key]
print("[i] retrieved codes for {0} language varieties".format(len(cols)))

# retrieve only annotated resources
rpl = {k: [] for k in cols}
tracker = collections.defaultdict(set)
for k, vals in progressbar(cols.items(), desc="retrieve annotated resources"):
    keep = []
    for v in vals:
        if data[v].get("hhtype") and not "(computerized assignment" in \
                data[v].get("hhtype", ""):
            if "author" in data[v]:
                authors = author_string(data[v]["author"])
                if not authors:
                    authors = [("", "")]
            elif "editor" in data[v]:
                authors = author_string(data[v]["editor"])
            else:
                authors = [("", "")]
            first, last = authors[0]
            if first and last and not "_" in first:
                if len(data[v].get("year", "")) == 4:
                    keep += [(v, authors[0][0] + "-" + data[v]["year"])]
                    tracker[authors[0][0] + "-" + data[v]["year"]].add(v)
    rpl[k] = keep


with open("map-data.tsv", "w") as f:
    f.write("Glottocode\tSources\tLatitude\tLongitude\tFamily\tMacroarea\n")
    for k, v in progressbar(rpl.items(), desc="write map data"):
        f.write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n".format(
            k, 
            len(v),
            glottocodes[k].latitude,
            glottocodes[k].longitude,
            glottocodes[k].family or "",
            glottocodes[k].macroareas[0].id))

print("retrieved codes and references")
# check for duplicats
# author, year, title
author = collections.defaultdict(list)
for key, book in data.items():
    if "lgcode" in book and "author" in book:
        persons = author_string(book["author"])
        for last, first in persons:
            author[last + " // " + first] += [key]

with open("authors.tsv", "w") as f:
    for name, books in sorted(author.items(), key=lambda x: len(x[1]),
                              reverse=True):
        f.write("{0[0]}\t{0[1]}\t{1}\n".format(
            name.split(" // "),
            len(books)))





# count sources for the 7580 languages
table = []
for code, refs in cols.items():
    if glottocodes[code].level.id == "language" and glottocodes[code].category == "Spoken L1 Language":
        table += [[code, len(refs)]]



my_table = {
        "ethnographic": [],
        "overview": [],
        "comparative": [],
        "dictionary": [],
        "wordlist": [],
        "grammar": [],
        "grammar_sketch": [],
        "text": [],
        }

mansi = []
resources = collections.defaultdict(list)
for ref in set(cols["mans1258"]):
    if not "author" in data[ref]:
        if "editor" in data[ref]:
            author = author_string(data[ref]["editor"])
        else:
            authors = []
    else:
        authors = author_string(data[ref]["author"])
    if "hhtype" in data[ref] and authors:
        hh = data[ref]["hhtype"]
        year = data[ref]["year"]
        title = data[ref]["title"]
        mansi += [[ref, authors[0][0], " AND ".join([", ".join(author) for
                                                     author in authors]), year, title, hh]]
        btk = authors[0][0] + "-" + year
        resources[btk] += [[" AND ".join([", ".join(author) for author in
                                          authors]), year, title, hh, ref]]

rtypes = collections.defaultdict(int)

with open("mansi-resources.tsv", "w") as f:
    for k, vals in sorted(resources.items(), key=lambda x: x[0]):
        if len(vals) > 1:
            dups = str(len(vals))
        else:
            dups = ""
        for val in vals:
            f.write(dups + "\t" + k + "\t" + "\t".join(val) + "\n")

            bits = val[-2].split(";")
            for bit in bits:
                if "(" in bit:
                    rtypes[bit.split(" ")[0] + "*"] += 1
                else:
                    rtypes[bit] += 1

for k in my_table:
    my_table[k] += [rtypes.get(k, 0), rtypes.get(k + '*', 0)]


resources = collections.defaultdict(list)
for ref in set(cols["phom1236"]):
    if not "author" in data[ref]:
        if "editor" in data[ref]:
            author = author_string(data[ref]["editor"])
        else:
            authors = []
    else:
        authors = author_string(data[ref]["author"])
    if "hhtype" in data[ref] and authors:
        hh = data[ref]["hhtype"]
        year = data[ref]["year"]
        title = data[ref]["title"]
        mansi += [[ref, authors[0][0], " AND ".join([", ".join(author) for
                                                     author in authors]), year, title, hh]]
        btk = authors[0][0] + "-" + year
        resources[btk] += [[" AND ".join([", ".join(author) for author in
                                          authors]), year, title, hh, ref]]

rtypes = collections.defaultdict(int)

with open("mansi-resources.tsv", "w") as f:
    for k, vals in sorted(resources.items(), key=lambda x: x[0]):
        if len(vals) > 1:
            dups = str(len(vals))
        else:
            dups = ""
        for val in vals:
            f.write(dups + "\t" + k + "\t" + "\t".join(val) + "\n")

            bits = val[-2].split(";")
            for bit in bits:
                if "(" in bit:
                    rtypes[bit.split(" ")[0] + "*"] += 1
                else:
                    rtypes[bit] += 1

for k in my_table:
    my_table[k] += [rtypes.get(k, 0), rtypes.get(k + '*', 0)]

out_table = []
for k, rows in my_table.items():
    out_table += [[k] + rows]

out_table += [[
    "References",
    sum([row[1] for row in out_table]),
    sum([row[2] for row in out_table]),
    sum([row[3] for row in out_table]),
    sum([row[4] for row in out_table])]]

table = r"""
\tabular{|l|ll|ll|}
\multirow{2}{*}{Information} &
\multicolumn{2}{c}{Northern Mansi} &
\multicolumn{2}{c}{Phom} \\\cline{2-4}
& Checked & Inferred & Checked & Inferred \\\hline
"""
for row in out_table:
    table += r"""{0} & {1} & {2} & {3} & {4} \\\hline""".format(
            row[0], row[1], row[2], row[3], row[3]) + "\n"
print(table)

