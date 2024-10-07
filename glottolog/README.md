# Code for the Bibliography in Glottolog

This code example explores the bibliography of [Glottolog 5.0](https://glottolog.org) and uses the tags provided by Glottolog to assign sources (bibliographic entries) to resources for individual languages. Since Glottolog's bibliography is not standardized in the sense of seeking to represent authors, places, and the like in a uniform way, the script also identifies a first set of resources (in the terminology of the CLD project) that would later need to be manually refined.

## Explore Data

Instead of pybtex, the current approach deliberately uses a regex-based parser,  is faster, but later, one should switch to a real bibtex parser, instead of the current solution.

The data is explored in several ways.

- sanity check for bibliographic entries, if author / editor and year are present, and if there is a datatype assigned (`hhtype`)
- keys are rendered as `author-year` to check if this way to render keys leads to distortions (apparently, these are minor)
- a map is created that shows the core references per language variety, using cartopy
