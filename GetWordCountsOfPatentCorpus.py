import urllib2
import re
import json
import random
from time import time
import os
from zipfile import ZipFile
import gzip
from joblib import Parallel, delayed  
import sys
import multiprocessing
import subprocess
from random import shuffle


class GetWordCountsOfPatentCorpus:
  def __init__(self):
    self.root_url = "http://www.google.com/googlebooks/uspto-patents-grants-text.html"
    self.download_root = "http://storage.googleapis.com/patents/grant_full_text/"
    self.total_bytes = 0
    self.dictionaries_path = "dictionaries"
    self.raw_data_path = "rawdata"
    self.extracted_path = "extracted"
    self.logs_path = "logs"
    self.gather_data = False
    self.preprocessed_path = "preprocessed"
    
  def get_patent_data(self):
    batch_of_files = self.get_batch()
    for file_name in batch_of_files:
      try:
        self.process_file(file_name)
      except:
        print "Could not process file: %s" % file_name
        log_file_path = os.path.join(self.logs_path, "unprocessed_files.txt")
        f = open(log_file_path, 'a')
        f.write(file_name + "\n")
        f.close()
      
    print "Total Downloaded File Size (GB): %f" % (float(self.total_bytes) / 1000000000)
  
  def process_file(self, file_name):
    print "Starting on file %s" % file_name
    self.download_zip(file_name)
    self.convert_zip_to_dictionary(file_name)
    os.remove(self.get_zip_file_path(file_name)) 
    
  def download_zip(self, file_name):
    url = self.download_root + file_name + ".zip"  
    print url
    u = urllib2.urlopen(url)
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (file_name, file_size)
    self.total_bytes += file_size
    
    file_size_dl = 0
    block_sz = 8192
    file_path = self.get_zip_file_path(file_name)
    f = open(file_path, 'wb')
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break
    
        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,
    
    f.close()
  
  def chunks(self, l, n):
    new_list = []
    for i in xrange(0, len(l), n):
        new_list.append(l[i:i+n])
    return new_list
  
  def get_batch(self):
    full_html = urllib2.urlopen(self.root_url).read()
    all_file_names = re.findall("(?<=" + self.download_root + ")(.*)(?=\.zip)", full_html)
    
    random.seed(42)
    shuffle(all_file_names)
    
    file_count = len(all_file_names)
    print "Total Number of Files: %d" % file_count
    batch_size = int(file_count / n_threads)
    batch_of_files = self.chunks(all_file_names, batch_size)[thread_id]
    print "Batch size: %d" % len(batch_of_files)
    #batch_of_files = batch_of_files[:3] # uncomment this for dry run
    return batch_of_files

  def get_zip_file_path(self, file_name):
    return os.path.join(self.raw_data_path, file_name.replace("/","_") + ".zip")

  def convert_zip_to_dictionary(self, file_name):
    zip_file = ZipFile(self.get_zip_file_path(file_name))
    members = zip_file.namelist()
    
    print "Building Dictionary: %s" % file_name
    word_frequency_dict = {}
    
    for i in range(len(members)):
      extracted_file_path = zip_file.extract(members[i], self.extracted_path)
      preprocessed_file_path = self.preprocess(os.path.split(extracted_file_path)[1])
      preprocessed_file = open(preprocessed_file_path, 'r')
      
      for line in preprocessed_file:
        raw_tokens = re.findall(r"[\w']+", line)
        tokens = [t.lower() for t in raw_tokens if t.isalpha()]
        
        for token in tokens:
          if token not in word_frequency_dict:
            word_frequency_dict[token] = 1
          else:
            word_frequency_dict[token] += 1
        
      preprocessed_file.close()
      os.remove(extracted_file_path)
      os.remove(preprocessed_file_path)
      
    dict_file_name = file_name.replace("/","_") + "_dict.json"
    dict_save_path = os.path.join(self.dictionaries_path, dict_file_name)
    f = open(dict_save_path, 'w')
    json.dump(word_frequency_dict, f)
    f.close()
  
  def filter_xml_markup(self, line):
    return re.sub(r'\<(.*?)\>', ' ', line)
  
  def preprocess(self, file_name):
    print "Preprocessing: %s" % file_name
    extracted_file_path = os.path.join(self.extracted_path, file_name)
    raw_file = open(extracted_file_path, "r")
    preprocessed_file_path = os.path.join(self.preprocessed_path, os.path.join(os.path.splitext(file_name)[0]) + "_preprocessed.txt") 
    extracted_file = open(preprocessed_file_path, "w")
    
    if file_name.startswith("ipg"):
      for line in raw_file:
        if "<claim-text>" in line:
          self.gather_data = True
        if "</claim-text>" in line:
          self.gather_data = False
          extracted_file.write(self.filter_xml_markup(line))
          
        if self.gather_data:
          extracted_file.write(self.filter_xml_markup(line))
          
    if file_name.startswith("pg"):
      for line in raw_file:
        if "<PTEXT>" in line:
          self.gather_data = True
        if "</PTEXT>" in line:
          self.gather_data = False
          extracted_file.write(self.filter_xml_markup(line))
          
        if self.gather_data:
          extracted_file.write(self.filter_xml_markup(line))

    if file_name.startswith("pftaps"):
      for line in raw_file:
        if line.startswith("PAL") or line.startswith("PAR"):
          extracted_file.write(line[3:])

    extracted_file.close()
    return preprocessed_file_path
      
def process_patent_batch(cmd):
    return subprocess.call(cmd, shell=False)

if __name__ == "__main__":
  if len(sys.argv) > 1:
    n_threads = int(sys.argv[1])
    thread_id = int(sys.argv[2])
    print "Running on thread %d of %d" % (thread_id, n_threads)
    
    gwc = GetWordCountsOfPatentCorpus()
    start = time()
    gwc.get_patent_data()
    end = time()
    minutes = (end-start)/60
    print "Thread finished in %f minutes." % minutes
  else:
    if not os.path.exists("extracted"):
      os.mkdir("extracted")
    if not os.path.exists("rawdata"):
      os.mkdir("rawdata")
    
    gwc = GetWordCountsOfPatentCorpus()
    
    if not os.path.exists(gwc.dictionaries_path):
      os.mkdir(gwc.dictionaries_path)
    
    if not os.path.exists(gwc.raw_data_path):
      os.mkdir(gwc.raw_data_path)
    
    if not os.path.exists(gwc.extracted_path):
      os.mkdir(gwc.extracted_path)
      
    if not os.path.exists(gwc.logs_path):
      os.mkdir(gwc.logs_path)
      
    if not os.path.exists(gwc.preprocessed_path):
      os.mkdir(gwc.preprocessed_path)
        
    num_cores = multiprocessing.cpu_count()
    print "number of cores: %d" % num_cores
    
    cmds = []
    for i in range(num_cores):
      cmd_args = ["python",  "GetWordCountsOfPatentCorpus.py"]
      cmd_args.append(str(num_cores))
      cmd_args.append(str(i))
      cmds.append(cmd_args)

    pool = multiprocessing.Pool(processes=num_cores)
    pool.map(process_patent_batch, cmds)