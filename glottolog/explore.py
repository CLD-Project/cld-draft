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
from clldutils.misc import slug
import json


def author_string(author, unify_authors, preprocess_authors):
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


with open("preprocessing.json") as f:
    prep = json.load(f)
    unify_authors = prep["authors"]
    preprocess_authors = prep["author_string"]
    basic_info_types = prep["bits"]

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
print("[i] retrieved codes for {0} language varieties".format(len(bib_by_variety)))

# retrieve only annotated resources
annotated = {k: [] for k in bib_by_variety}
computed = {k: [] for k in bib_by_variety}
tracker_annotated = collections.defaultdict(set)
tracker_computed = collections.defaultdict(set)
for key, vals in progressbar(bib_by_variety.items(), desc="retrieve annotated resources"):
    keep_annotated = []
    keep_computed = []
    for value in vals:
        annotation = bib_by_source[value].get("hhtype", "")
        year = bib_by_source[value].get("year", "")
        title = bib_by_source[value].get("title", "").strip()
        creators = [("", "")]
        if "author" in bib_by_source[value]:
            creators = author_string(bib_by_source[value]["author"],
                                     unify_authors, preprocess_authors)
        elif "editor" in bib_by_source[value]:
            creators = author_string(bib_by_source[value]["editor"],
                                     unify_authors, preprocess_authors)
        if not creators:
            creators = [("", "")]
        family_name, first_name = creators[0]
        if family_name and first_name and len(year) == 4 and year.isdigit() and title:
            book_key = family_name.replace(" ", "_") + "-" + year + "-" + "_".join([
                slug(s) for s in title.split()[:4]])
            if "(computerized assignment" in annotation:
                keep_computed += [(value, book_key)]
                tracker_computed[book_key].add(value)
            elif annotation:
                keep_annotated += [(value, book_key)]
                tracker_annotated[book_key].add(value)
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
    for k, v in progressbar(annotated.items(), desc="write map data (annotated)"):
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
    for k, v in progressbar(computed.items(), desc="write map data (computed)"):
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
for area, (a, c) in by_area.items():
    table += [[area, mean(a), median(a), stdev(a), mean(c), median(c),
               stdev(c)]]

result = tabulate(table, floatfmt=[".2f"] , tablefmt="pipe", headers="firstrow")


print("[i] table of average number of resources per variety")
print(result)



# make a list of authors that is "cleaned"
selection_annotated, selection_computed = {}, {}
for key, valueset in tracker_annotated.items():
    for value in valueset:
        selection_annotated[value] = key
for key, valueset in tracker_computed.items():
    for value in valueset:
        selection_computed[value] = key

with open("statistics.md", "w") as f:
    f.write("# Sources Per Variety\n\n")
    f.write(result)
    f.write("\n")
    f.write("# Basic Statistics\n\n")
    f.write(
            tabulate([
                ["Key", "Value"],
                ["Language Varieties", len(bib_by_variety)],
                ["References (Unique)", len(tracker_annotated) + len(tracker_computed)],
                ["References (Annotated)", len(tracker_annotated)],
                ["References (Computed)", len(tracker_computed)],
                ["Sources (Non-Unique)", len(selection_annotated) + len(selection_computed)],
                ["Sources (Annotated)", len(selection_annotated)],
                ["Sources (Computed)", len(selection_computed)],
                ],
                     tablefmt="pipe",
                     headers="firstrow",
                     floatfmt=".2f"))

# check for duplicats
# author, year, title
author_annotated = collections.defaultdict(list)
author_computed = collections.defaultdict(list)
for key, book in bib_by_source.items():
    if key in selection_annotated:
        cleaned_key = selection_annotated[key]
        if "author" in book:
            persons = author_string(book["author"], unify_authors,
                                    preprocess_authors)
        else:
            persons = author_string(book["editor"], unify_authors,
                                    preprocess_authors)
        for last, first in persons:
            author_annotated[last + " // " + first] += [cleaned_key]
    if key in selection_computed:
        cleaned_key = selection_computed[key]
        if "author" in book:
            persons = author_string(book["author"], unify_authors,
                                    preprocess_authors)
        else:
            persons = author_string(book["editor"], unify_authors,
                                    preprocess_authors)
        for last, first in persons:
            author_computed[last + " // " + first] += [cleaned_key]

all_authors = collections.defaultdict(lambda : [[], []])
for name, books in author_annotated.items():
    all_authors[name][0] = books
for name, books in author_computed.items():
    all_authors[name][1] = books


with open("authors.tsv", "w") as f:
    f.write("Family_Name\tName\tResources_Annotated\tSources_Annotated\tResources_Computed\tSources_Computed\n")
    for name, books in sorted(all_authors.items(), key=lambda x: len(set(x[1][0])),
                              reverse=True):
        f.write("{0[0]}\t{0[1]}\t{1}\t{2}\t{3}\t{4}\n".format(
            name.split(" // "),
            len(set(books[0])),
            len(books[0]),
            len(set(books[1])),
            len(books[1])
            ))

# store data for the different parts (write "resource" table and link to
# sources)

resources = collections.defaultdict(lambda : {"languages": [], "sources": [],
                                              "types": []})
for language, keys in bib_by_variety.items():
    for key in keys:
        rkey = False
        if key in selection_annotated:
            rtype = "annotated"
            rkey = selection_annotated[key]
        if key in selection_computed:
            rtype = "computed"
            rkey = selection_computed[key]
        if rkey:
            resources[rkey]["languages"] += [language]
            resources[rkey]["sources"] += [key]
            resources[rkey]["types"] += [rtype]

# write preliminary list of references to file / extract glottolog information
reference_dict = collections.defaultdict(list)
for key, vals in resources.items():
    languages = {k: [] for k in set(vals["languages"])}
    for i in range(len(vals["languages"])):
        languages[vals["languages"][i]] += [(key, vals["sources"][i],
                                             vals["types"][i],
                                             bib_by_source[vals["sources"][i]]["hhtype"]
                                             )]
    for language, info in languages.items():
        reference_dict[language] += info

# the references now assemble the cleaned key plus the description
# the next step consists in harmonizing the assignments and then extracting
# both the references and the resources from there

# write data to file now, or ideally, just create a database
# merge sources that are merged to identical keys
reference_table = []
visited_resources = set()
for key, vals in reference_dict.items():
    # here, assemble by vals[1]
    recs = collections.defaultdict(lambda : {"bit": collections.defaultdict(list),
                                    "sources": []})
    for val in vals:
        recs[val[0]]["sources"] += [val[1]]
        recs[val[0]]["bit"][val[3]] += [val[2]]
    for k, info in recs.items():
        for bit, status in info["bit"].items():
            if len(set(status)) == 2:
                status = "annotated"
            elif len(set(status)) == 1:
                status = status[0]
            if status == "annotated":
                bits = bit.split(";")
            else:
                bits = [bit]
            for bit_ in bits:
                # retrieve the cleaned bits
                dok, bit_norm = basic_info_types[bit_]
                if dok:
                    reference_table += [[
                        key, # language_id
                        k, # resource_id
                        dok,
                        bit_norm,
                        status
                        ]]
                    visited_resources.add(k)

resource_table = []
for key, vals in resources.items():
    if key in visited_resources:
        # take first source and extract author and title
        sources = [bib_by_source[v] for v in vals["sources"]]
        authors = [source.get("author", source.get("editor", "")) for source in
                  sources]
        titles = [source["title"] for source in sources]
        years = [source["year"] for source in sources]

        if len(set(authors)) > 1:
            author_variants = " // ".join(sorted(set(authors)))
        else:
            author_variants = ""
        if len(set(titles)) > 1:
            title_variants = " // ".join(sorted(set(titles)))
        else:
            title_variants = ""

        resource_table += [[
            key,
            authors[0],
            author_variants,
            titles[0],
            title_variants,
            years[0],
            " ".join(vals["sources"])
            ]]

with open("resources.tsv", "w") as f:
    f.write("\t".join([
        "ID", "Creators", "Creator_Variants", "Title", "Title_Variants",
        "Year", "Sources"]) + "\n")
    for row in resource_table:
        f.write("\t".join(row) + "\n")

with open("references.tsv", "w") as f:
    f.write("\t".join([
        "ID", "Language_ID", "Reference_ID", "DomainOfKnowledge", "BasicInformationType", "Status"]) + "\n")
    current_language = ""
    idx = 1
    for row in sorted(reference_table):
        if row[0] != current_language:
            current_language = row[0]
            idx = 1
        else:
            idx += 1
        key = current_language + "-" + str(idx)
        f.write(key + "\t" + "\t".join(row) + "\n")



# reference table must now be created for a particular glottocode

input("stop here")

# count individual sources for Mansi and the Phom
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

