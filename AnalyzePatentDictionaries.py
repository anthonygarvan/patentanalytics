import os
import json
from time import time
import operator
from random import shuffle

class AnalyzePatentDictionaries:
  def __init__(self):
    self.dictionaries_path = "dictionaries"
    self.results_path = "results"
    self.dictionaries_by_year_path = os.path.join(self.results_path, "dictionaries_by_year_2.json")
    
    if not os.path.exists(self.results_path):
      os.mkdir(self.results_path)
  
  def process_dictionaries(self):
    dictionaries_by_year = self.get_dictionaries_by_year()
    early_dict = self.get_era_dictionary(dictionaries_by_year, 1975, 1980)
    recent_dict = self.get_era_dictionary(dictionaries_by_year, 2005, 2015)
    dict_diff = self.get_difference(early_dict, recent_dict)
    words_of_interest = self.get_words_of_interest(dict_diff)
    normalized_dictionaries_by_year = self.normalize_dictionaries_by_year(dictionaries_by_year)
    self.save_word_trends(normalized_dictionaries_by_year, words_of_interest)
    self.get_wordle_format(words_of_interest, recent_dict)
  def get_new_words_dictionary(self, old_words, dictionaries_by_year):
    new_words_dictionary = {}
    
    for year in dictionaries_by_year:
      if int(year) > self.cutoff_year:
        for token in dictionaries_by_year[year]:
          if token not in old_words:
            if token not in new_words_dictionary:
              new_words_dictionary[token] = dictionaries_by_year[year][token]  
            else:
              new_words_dictionary[token] += dictionaries_by_year[year][token]
    
    return new_words_dictionary
    
  def get_dictionaries_by_year(self):
    print "Getting dictionaries by year..."
    if not os.path.exists(self.dictionaries_by_year_path):
      file_names = os.listdir(self.dictionaries_path)
      shuffle(file_names)
      #file_names = file_names[:100]
      
      dictionaries_by_year = {}
      num_files = len(file_names)
      for i in range(num_files):
        file = file_names[i]
        print "Processing File %d of %d: %s" % (i, num_files, file)
        file_path = os.path.join(self.dictionaries_path, file)
        f = open(file_path, 'r')
        new_dict = json.load(f)
        
        year = file.split('_')[0]
        if year not in dictionaries_by_year:
          dictionaries_by_year[year] = {}
          
        dictionaries_by_year[year] = self.merge_dictionary(dictionaries_by_year[year], new_dict)
      print "Years Processed: %s" % str(dictionaries_by_year.keys())
      f = open(self.dictionaries_by_year_path, 'w')
      json.dump(dictionaries_by_year, f)
    else:
      f = open(self.dictionaries_by_year_path, 'r')
      dictionaries_by_year = json.load(f)
    return dictionaries_by_year
    
  def merge_dictionary(self, dict, new_dict):
    for key in new_dict:
      if key in dict:
        dict[key] += new_dict[key]
      else:
        dict[key] = new_dict[key]
    return dict
    
  def get_era_dictionary(self, dictionaries_by_year, start_year, end_year):
    print "Getting existing words..."
    years = [y for y in dictionaries_by_year.keys() if ((int(y) < end_year) and (int(y) > start_year))]
    
    era_dict = {}
    for year in years:
      era_dict = self.merge_dictionary(era_dict, dictionaries_by_year[year])
    print "Number of words used in the range %d to %d: %d" % (start_year, end_year, len(era_dict))  
    return era_dict
    
  def get_difference(self, old_dict, new_dict):
    dict_diff = {}
    
    """
    for key in new_dict:
      if key in old_dict:
        dict_diff[key] = float(new_dict[key])/(float(old_dict[key])+1)
      else:
        dict_diff[key] = float(new_dict[key])
    """
    
    for key in new_dict:
      if key not in old_dict:
        dict_diff[key] = new_dict[key]
    return dict_diff
    
  def normalize_dictionaries_by_year(self, dictionaries_by_year):
    normalized_dictionaries_by_year = {}
    for year in dictionaries_by_year:
      normalized_dictionaries_by_year[year] = self.normalize_dict(dictionaries_by_year[year])
      
    return normalized_dictionaries_by_year
    
  def normalize_dict(self, dict):
    normalized_dict = {}
    sum = 0
    for token in dict:
      sum += dict[token]
    for token in dict:
      normalized_dict[token] = float(dict[token]) / float(sum)
      
    return normalized_dict
    
  def get_words_of_interest(self, dict):
    sorted_dict = sorted(dict.items(), key=operator.itemgetter(1), reverse=True)
    print "Number of new words: %d" % len(sorted_dict)
    sorted_dict_sample = sorted_dict[:500]
    
    f = open("results/differences.json", 'w')
    json.dump(sorted_dict_sample, f)
    f.close()
    
    return [t[0] for t in sorted_dict_sample]
  
  def get_wordle_format(self, words_of_interest, dictionary):
    f = open(os.path.join(self.results_path, "wordle.txt"), 'w')
    for word in words_of_interest:
      line = "%s:%s\n" % (word, dictionary[word])
      f.write(line)
    f.close()
    
  def filter_bad_data(self, dictionaries_by_year, words_of_interest):
    years = sorted(dictionaries_by_year.keys())
    excluded = set()
    for word in words_of_interest:
      for i in range(1, len(years)-1):
        last_year = years[i-1]
        this_year = years[i]
        next_year = years[i+1]
        last_value = dictionaries_by_year[last_year][word] if word in dictionaries_by_year[last_year] else 1
        this_value = dictionaries_by_year[this_year][word] if word in dictionaries_by_year[this_year] else 1
        next_value = dictionaries_by_year[next_year][word] if word in dictionaries_by_year[next_year] else 1
        
        old_diff = float(this_value) / float(last_value)
        new_diff = float(next_value) / float(this_value)
        
        if (old_diff > 100 and new_diff < 2):
          if word not in excluded:
            excluded.add(word)
        
    new_words_of_interest = [w for w in words_of_interest if w not in excluded]
    print new_words_of_interest[:10]
    return new_words_of_interest
        
  def save_word_trends(self, dictionaries_by_year, words):
    years = sorted(dictionaries_by_year.keys())
    
    f = open("results/word_trends.csv", "w")
    line = "Year,"
    for word in words:
      line += "%s," % word
    line += "\n"
    f.write(line)
    
    for year in years:      
      line = "%s," % year
      for word in words:
        if word in dictionaries_by_year[year]:
          line += "%f," % dictionaries_by_year[year][word]
        else:
          line += "%f," % 0
      line += "\n"
      f.write(line)
    f.close()
    
if __name__ == "__main__":
  apd = AnalyzePatentDictionaries()
  start = time()
  apd.process_dictionaries()
  end = time()
  minutes = (end-start)/60
  print "Analysis finished in %f minutes." % minutes

