This is a project for doing awesome analytics on publicly available patent data.

To run, use

python GetWordCountsOfPatentCorpus.py

This takes about 90 minutes to run on a quad-core machine with a cloud-grade 
internet connection. It's pretty verbose. It streams all processing, so it will 
only take up as much space as the final dictionaries (~ 1 GB). This script generates
term frequency dictionary per week from 1976-present.

Next, to generate the word cloud data to feed into wordle, along with some trend
data, run

python AnalyzePatentDictionaries.py

The first time you run this, it will aggregate the weekly dictionaries into a single
object which is a dictionary of dictionaries aggregated by year. It will store
that dictionary as a result on the disk. After that first run, it will just load up
that dictionaries_by_year dictionary from disk rather than recompute it all. 

If you find any bugs or have any questions, please let me know.