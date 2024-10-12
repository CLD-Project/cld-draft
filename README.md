# Initial Tests on Data Model and Data for the CLD Project

This repository provides some initial overview on tests and ideas regarding the data model and the data itself that we intent to model and assemble within the CLD project. Most notably, the repository provides an initial estimate regarding the core languages in Glottolog that should be assembled as part of the CLD project, along with an initial investigation of the sources per language that Glottolog assembles. 

![Base Map of the Languages in the CLD Project](maps/map.jpg)

## Detailed Statistics for Inspection

For details, check the overview on:

* [Languages by Macro-Area](glottolog/languages.md#languages-by-macro-area)
  - [Macro-Area Eurasia](glottolog/languages.md#macro-area-eurasia)
  - [Macro-Area North America](glottolog/languages.md#macro-area-north-america)
  - [Macro-Area South America](glottolog/languages.md#macro-area-south-america)
  - [Macro-Area Australia](glottolog/languages.md#macro-area-australia)
  - [Macro-Area Africa](glottolog/languages.md#macro-area-africa)
  - [Macro-Area Papunesia](glottolog/languages.md#macro-area-papunesia)
* [Sources Per Variety](glottolog/statistics.md#sources-per-variety)
* [Basic Statistics](glottolog/statistics.md#basic-statistics)

## Running the Code Examples

We have created a Makefile that should make it easy to run the code shown here. We suppose that you are able to install the requirements (including the package [cartopy](https://pypi.org/project/cartopy) and that you are using a fresh virtual environment instead of the basic Python installation of your computer.

To install all packages, you can just type:

```shell
$ make install-requirements
```

To create the base map of all languages by macro-area, you can type:

```shell
$ make cld-map
```

For details, inspect the information in the [README](maps/README.md) in the folder `maps`.

To re-run the basic code that explores the Glottolog bibliography, type:

```shell
$ make cld-test-corpus
```

This will recreate several data files from the data. It requires that you run some specific configuration explained in the [README](glottolog/README.md) of the folder `glottolog`.

To run our workflow examples, just type:

```shell
$ make cld-workflow
```

For details, check the [README](workflow/README.md) in the folder `workflow`.
