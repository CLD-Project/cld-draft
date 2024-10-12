# Workflow for Initial Assembly of Data from Glottolog for the Curation of the CLD Corpus

This worfklow starts from the script `get_references.py` that takes a Glottocode as parameter form the commandline.

Thus, running:

```shell
$ python get_references.py phom1236
```

Will create new files for the language Phom, that you can inspect. All files start with the Glottocode, and the script creates a BibTeX file [`phom1236-sources.bib`](phom1236-sources.bib), a file for the references [`phom1236-references.tsv`](phom1236-references.tsv) and a file for the resources [`phom1236-resources.tsv`](phom1236-resources.tsv). 
Data has been calculated in an exemplary manner for `phom1236` and `mans1258`. 
