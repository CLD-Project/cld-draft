import collections
import re
from pyglottolog import Glottolog
from pyglottolog.references.bibfiles import Entry
from tqdm import tqdm as progressbar
from zipfile import ZipFile
from pathlib import Path
from cldfcatalog import Config
from statistics import mean, median, stdev
from tabulate import tabulate

preprocess_authors = {
        "Hall and A., Robert and Jr.": "Hall Junior, Robert A.",
        "Joyce Huckett and Awadoudo and Huckett Adiguma and Awadoudo Joyce and Adiguma and Laumamala": \
                "Huckett, Joyce and Navakwaya, Fuwali and Awadoudo, Adilo'a",

        }

unify_authors = {
        "Kari, James (interviewer)": "Kari, James",
        "others": None,
        "trans.": None,
        "____": None,
        "____ ____": None,
        "No Author Stated": "Anonymous, Unknown Author",
        "Anonymous": "Anonymous, Unknown Author",
        "[Anonymous]": "Anonymous, Unknown Author",
        "Unknown Author": "Anonymous, Unknown Author",
        "Author Unknown": "Anonymous, Unknown Author",
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

bib_by_source = collections.defaultdict(dict)
bib_by_variety = collections.defaultdict(list)

for row in progressbar(lines, desc="parsing bibtex"):
    if row.startswith("@"):
        key = row.split("{")[1].strip()[:-1]
    if row.startswith("   ") and " = {" in row:
        parts = row.strip().split(" = {")
        attr, val = parts[0], " = {".join(parts[1:])
        bib_by_source[key][attr] = val.strip("},")
    if "lgcode = " in row:
        codes = row.strip().split(" = {")[1][:-2]
        ncodes = Entry.lgcodes(codes)
        for ncode in ncodes:
            if ncode in glottocodes:
                if glottocodes[ncode].category == "Spoken L1 Language" and \
                        glottocodes[ncode].macroareas:
                    bib_by_variety[glottocodes[ncode].glottocode] += [key]
print("[i] retrieved codes for {0} language varieties".format(len(cols)))

# retrieve only annotated resources
annotated = {k: [] for k in cols}
computed = {k: [] for k in cols}
tracker = collections.defaultdict(set)
for key, vals in progressbar(cols.items(), desc="retrieve annotated resources"):
    keep_annotated = []
    keep_computed = []
    for value in vals:
        annotation = bib_by_source[value].get("hhtype", "")
        year = bib_by_source[value].get("year", "")
        creators = [("", "")]
        if "author" in data[value]:
            creators = author_string(bib_by_source[value]["author"])
        elif "editor" in data[value]:
            creators = author_string(bib_by_source[value]["editor"])
        if not creators:
            creators = [("", "")]
        family_name, first_name = creators[0]
        if family_name and first_name and len(year) == 4:
            tracker[family_name + "-" + year].add(value)
            if "(computerized assignment" in annotation:
                keep_computed += [(value, family_name + "-" + year)]
            elif annotation:
                keep_annotated += [(value, family_name + "-" + year)]

    annotated[key] += keep_annotated
    computed[key] += keep_computed


# count the average numbers per variety
annotated_resources, computed_resources = [], []
by_area = {
        "eurasia": [[], []],
        "northamerica": [[], []],
        "southamerica": [[], []],
        "australia": [[], []],
        "pacific": [[], []],
        "africa": [[], []]
        }

with open("map-data-annotated.tsv", "w") as f:
    f.write("Glottocode\tSources\tLatitude\tLongitude\tFamily\tMacroarea\n")
    for k, v in progressbar(annotated.items(), desc="write map data"):
        f.write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n".format(
            k, 
            len(v),
            glottocodes[k].latitude,
            glottocodes[k].longitude,
            glottocodes[k].family or "",
            glottocodes[k].macroareas[0].id))
        annotated_resources += [len(v)]
        by_area[glottocodes[k].macroareas[0].id][0] += [len(v)]

with open("map-data-computed.tsv", "w") as f:
    f.write("Glottocode\tSources\tLatitude\tLongitude\tFamily\tMacroarea\n")
    for k, v in progressbar(computed.items(), desc="write map data"):
        f.write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n".format(
            k, 
            len(v),
            glottocodes[k].latitude,
            glottocodes[k].longitude,
            glottocodes[k].family or "",
            glottocodes[k].macroareas[0].id))
        computed_resources += [len(v)]
        by_area[glottocodes[k].macroareas[0].id][1] += [len(v)]

print("retrieved codes and references")
table = [
        ["Subset", "Mean (A)", "Median (A)", "STD (A)", "Mean (C)", "Median (C)", "STD (C)"],
        [
            "all", 
            mean(annotated_resources), 
            median(annotated_resources),
            stdev(annotated_resources), 
            mean(computed_resources), 
            median(computed_resources),
            stdev(computed_resources)],
        ]
for area, (a, c) in by_area:
    table += [[area, mean(a), median(a), stdev(a), mean(c), median(c),
               stdev(c)]]

result = tabulate(table, floatfmt=".2f", tablefmt="pipe")
with open("statistics.md", "w") as f:
    f.write(result)
print(result)




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

