# Patent Analytics

## Goal
This is a project for doing awesome analytics on publicly available patent data.

It currently outputs a word cloud of the most popular words today that didn't exist
in the 1970s, and also a csv summarizing the trends of those words from 1976 - present.

### Running
To run, use
```bash
python GetWordCountsOfPatentCorpus.py
```
This script generates term frequency dictionary per week from 1976-present.
As intermediate steps, it downloads the files from google, unzips them, extracts
the text portions (it uses the file name to detect which format it is in). When 
getting the word counts, it does not stem the words (ie., "browser" is read as a
different word from "browsers"), although it does lower case and ignore non-alphabetical
tokens.

This takes about 90 minutes to run on a quad-core machine with a cloud-grade 
internet connection. It's pretty verbose. It streams all processing, so it will 
only take up as much disk space as the final dictionaries (~ 1 GB). 

Next, to generate the word cloud data to feed into wordle, along with some trend
data, run

```bash
python AnalyzePatentDictionaries.py
```
The first time you run this, it will aggregate the weekly dictionaries into a single
object which is a dictionary of dictionaries aggregated by year. It will store
that dictionary as a result on the disk. After that first run, it will just load up
that dictionaries_by_year dictionary from disk rather than recompute it all. 

### Bugs and Questions
If you find any bugs or have any questions, please let me know.