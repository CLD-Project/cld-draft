# Code for the Bibliography in Glottolog

This code example explores the bibliography of [Glottolog
5.0](https://glottolog.org) and uses the tags provided by Glottolog to assign
sources (bibliographic entries) to resources for individual languages. Since
Glottolog's bibliography is not standardized in the sense of seeking to
represent authors, places, and the like in a uniform way, the script also
identifies a first set of resources (in the terminology of the CLD project)
that would later need to be manually refined.

## Installation of Required Packages

In order to install the packages required to run the analysis exemplified here, we recommend to use `pip` in Python, with a [fresh virtual environment]().

```shell
$ pip install -r requirements.txt
```

Once this has been done, you must make sure to obtain the data from Glottolog. This can be done with the help of a [`cldfbench`](https://pypi.org/project/cldfbench) command that will download the GIT repository and store the path on your system for the use in the main script `explore.py`.

```
$ cldfbench catconfig
```

You will be prompted to answer questions. Please make sure to confirm that Glottolog be cloned to your system (this requires about 1GB of space).

## Running the Main Script for Data Exploration

The script `explore.py` runs a detailed analysis of the bibliography underlying Glottolog. It loads the bibliography, searches for annotations for individual languages to which bibliographic items have been assigned, conducts an initial mapping of *basic information types* in Glottolog with the targeted *basic information types* in the CLD project, and finally creates tables for references and resources that link to the bibliography, along with a detailed summary statistics on all macro-areas in the data. To run the script, simply type the following in the terminal.

```shell
$ python explore.py
```

The resulting statistics are shared in different files. The file `languages.md` contains detailed statistics on sources per macro area. The file `statistics.md` summarizes major statistics (annotated and computationally assigned sources for individual languages across macro-areas). 

## Technical Information on the Script

The script parses the information in the zipped BibTex-File containing all entries of the Glottolog-Bibliography. 
It then uses basic string manipulation techniques to verify basic aspects of the bibliographic information (valid author names, valid years, valid titles), in order to conduct a first search of valid titles for individual languages in the data. It also selects all languages in Glottolog that we plan to annotate for the CLD project. The resulting data is then written to several files and presented in condensed form in tables that we use to derive additional statistics or create a map of all languages in the sample, colored by macro-area.


