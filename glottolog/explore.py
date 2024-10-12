import collections
import re
from pyglottolog import Glottolog
from pyglottolog.references.bibfiles import Entry
from tqdm import tqdm as progressbar
import zipfile
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


def project_path(*paths):
    return Path(__file__).parent.joinpath(*paths)


with open(project_path("preprocessing.json")) as f:
    prep = json.load(f)
    unify_authors = prep["authors"]
    preprocess_authors = prep["author_string"]
    basic_info_types = prep["bits"]

cfg = Config.from_file()
g_ = Glottolog(cfg.get_clone("glottolog"))
glottocodes = g_.languoids_by_code()

print("[i] loaded Glottolog data")

if not project_path("glottolog-5.0.bib").exists():
    with zipfile.ZipFile(project_path("glottolog-5.0.bib.zip")) as zf:
        with zf.open("glottolog-5.0.bib") as f:
            lines = [row.decode("utf-8") for row in f]
    print("[i] loaded bibliography from zip-file")
else:
    with open(project_path("glottolog-5.0.bib")) as f:
        lines = [row for row in f]
    print("[i] loaded bibliography from BibTeX-file")

bib_by_source = collections.defaultdict(dict)
bib_by_variety = collections.defaultdict(list)
languages = {}

for row in progressbar(lines, desc="parsing bibtex"):
    if row.startswith("@"):
        key = row.split("{")[1].strip()[:-1]
        btype = row[1: row.index("{")]
        bib_by_source[key]["bibtex_type"] = btype
    if row.startswith("   ") and " = {" in row:
        parts = row.strip().split(" = {")
        attr, val = parts[0], " = {".join(parts[1:])
        bib_by_source[key][attr] = val.strip("},")
    if "lgcode = " in row:
        codes = row.strip().split(" = {")[1][:-2]
        ncodes = set(Entry.lgcodes(codes))
        for ncode in ncodes:
            if ncode in glottocodes:
                if glottocodes[ncode].category == "Spoken L1 Language" and \
                        glottocodes[ncode].macroareas:
                    gcode = glottocodes[ncode].glottocode
                    bib_by_variety[gcode] += [key]

languages = {}
for gcode, sources in progressbar(bib_by_variety.items(), desc="parsing glottolog"):
    languages[gcode] = {
            "name": glottocodes[gcode].name,
            "family": glottocodes[gcode].family.name if glottocodes[gcode].family else "",
            "latitude": glottocodes[gcode].latitude,
            "longitude": glottocodes[gcode].longitude,
            "macroarea": glottocodes[gcode].macroareas[0].name,
            "sources": len(sources),
            }

# basic statistics
all_sources, all_sources_annotated, all_sources_with_tag = set(), set(), set()
sources_with_tag_and_bit = set()
for k, vals in bib_by_variety.items():
    for v in vals:
        all_sources.add(v)
        if bib_by_source[v].get("hhtype"):
            all_sources_with_tag.add(v)
        if not 'computerized' in bib_by_source[v]['lgcode']:
            all_sources_annotated.add(v)

table =[
        ["Key", "Value"],
        ["Sources", len(bib_by_source)],
        ["Sources with Language", len([s for s in bib_by_source.values() if
                                   s.get("lgcode")])],
        ["Sources with Language (Manually Assigned)", len([s for s in
                                               bib_by_source.values() if
                                               s.get("lgcode") and not
                                               "computerized" in
                                               s["lgcode"]])],
        ["Sources with Tag", len([s for s in bib_by_source.values() if
                              s.get('hhtype')])],
        ["Sources with Tag (Manually Tagged)", len([s for s in bib_by_source.values() if
                                          s.get('hhtype') and not
                                          'computerized' in s.get('hhtype',
                                                                  '')])],
        ["Sources assigned to L1 Language", len(all_sources)],
        ["Sources assigned to L1 Language (Manually Assigned)",
         len(all_sources_annotated)],
        ["Sources assigned to L1 Language with Tag",
         len(all_sources.intersection(all_sources_with_tag))],
        ["Sources assigned to L1 Language (Manually Assigned) with Tag", 
         len(all_sources_annotated.intersection(all_sources_with_tag))],
        ]
with open(project_path("sources.md"), "w") as f:
    f.write("# Statistics on Glottolog Bibliography\n\n")
    f.write(tabulate(table, tablefmt="pipe", headers="firstrow"))

# write to file
with zipfile.ZipFile(project_path().parent.joinpath("workflow", "glottolog.json.zip"), mode="w",
                     compression=zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("glottolog.json", json.dumps({"varieties": bib_by_variety, "sources": bib_by_source,
              "languages": languages}))
    
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
                slug(s) for s in title.split()[:3]])
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
        "Eurasia": [[], []],
        "North America": [[], []],
        "South America": [[], []],
        "Australia": [[], []],
        "Africa": [[], []],
        "Papunesia": [[], []],
        }

with open(project_path().parent.joinpath("maps", "map-data-annotated.tsv"), "w") as f:
    f.write("Glottocode\tSources\tLatitude\tLongitude\tFamily\tMacroarea\n")
    for k, v in progressbar(annotated.items(), desc="write map data (annotated)"):
        f.write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n".format(
            k, 
            len(v),
            glottocodes[k].latitude,
            glottocodes[k].longitude,
            glottocodes[k].family or "",
            glottocodes[k].macroareas[0].name))
        annotated_resources += [len(v)]
        by_area[glottocodes[k].macroareas[0].name][0] += [len(v)]

with open(project_path().parent.joinpath("maps", "map-data-computed.tsv"), "w") as f:
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
        by_area[glottocodes[k].macroareas[0].name][1] += [len(v)]

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

selected_sources = {k: v for k, v in selection_annotated.items()}
selected_sources.update(selection_computed)

with open(project_path("statistics.md"), "w") as f:
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
                     floatfmt=".2f")
            )

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


with open(project_path("authors.tsv"), "w") as f:
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
    langs = {k: [] for k in set(vals["languages"])}
    for i in range(len(vals["languages"])):
        langs[vals["languages"][i]] += [(key, vals["sources"][i],
                                             vals["types"][i],
                                             bib_by_source[vals["sources"][i]]["hhtype"]
                                             )]
    for language, info in langs.items():
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

with open(project_path().parent.joinpath("workflow", "resources.tsv"), "w") as f:
    f.write("\t".join([
        "ID", "Creators", "Creator_Variants", "Title", "Title_Variants",
        "Year", "Sources"]) + "\n")
    for row in resource_table:
        f.write("\t".join(row) + "\n")

with open(project_path().parent.joinpath("workflow", "references.tsv"), "w") as f:
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

# write macroarea to file
with open(project_path("languages.md"), "w") as f:
    f.write("# Languages by Macro-Area\n\n")
    for macroarea in ["Eurasia", "North America", "South America", "Australia",
                      "Africa", "Papunesia"]:
        ma_data = {k: v for k, v in languages.items() if v["macroarea"] ==
                   macroarea}

        f.write("## Macro-Area " + macroarea + "\n\n")
        f.write("### Basic Statistics\n\n")

        varieties = len(ma_data)
        sources = sum([v["sources"] for v in ma_data.values()])
        sources_target = sum([len(
            [s for s in bib_by_variety[k] if s in
                                 selection_annotated or s in
             selection_computed]) for k in ma_data])
        sources_annotated = sum([len(
            [s for s in bib_by_variety[k] if s in
                                 selection_annotated]) for k in ma_data])
        sources_computed = sum([len(
            [s for s in bib_by_variety[k] if s in
                                 selection_computed]) for k in ma_data])
        
        f.write(tabulate([
            ["Varieties", varieties],
            ["Sources (all)", sources],
            ["Sources per Variety (all)", "{0:.2f}".format(sources / varieties)],
            ["Sources (Target Corpus)", sources_target],
            ["Sources per Variety (Target Corpus)", "{0:.2f}".format(sources_target / varieties)],
            ["Sources (annotated)", sources_annotated],
            ["Sources per Variety (annotated)", "{0:.2f}".format(sources_annotated / varieties)],
            ["Sources (computed)", sources_computed],
            ["Sources per Variety (computed)", "{0:.2f}".format(sources_computed / varieties)],
            ],
                         tablefmt="pipe", headers = ["Key", "Value"]))
        f.write("\n\n\n")
        f.write("### Languages by Family\n\n")

        by_fam = collections.defaultdict(int)
        for k, v in ma_data.items():
            by_fam[v["family"]] += 1
        table = [["Language Family", "Varieties"]]
        for family, varieties in sorted(by_fam.items(), key=lambda x: x[1],
                                        reverse=True):
            table += [[family if family else "Isolates", varieties]]
        table += [["Total", sum(by_fam.values())]]
        f.write(tabulate(table, tablefmt='pipe', headers='firstrow'))
        f.write("\n\n\n")

