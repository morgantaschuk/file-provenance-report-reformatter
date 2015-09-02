#!/oicr/local/sw/Python-2.7.2/bin/python2.7
from __future__ import print_function

import sys,getopt,time
import subprocess
import csv,re
import os
import gzip
from zipfile import ZipFile
from datetime import datetime

def usage(long_opts):
   print('basic_stats.py',"--"+" --".join(long_opts).replace("="," <val>"))
   print('Gather library-level metrics from DNA and RNA libraries, print total bases aligned and total libraries')
   print('   use -h to print this message')

def main(argv):
   sw_filename=None
   long_opts=["use-sw-file="]
   try:
      opts, args = getopt.getopt(argv,"h",long_opts)
   except getopt.GetoptError:
      usage(long_opts)
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         usage(long_opts)
         sys.exit()
      elif opt == '--use-sw-file':
         sw_filename=arg
   if sw_filename is None:
         usage(long_opts)
         sys.exit()
                 #store: date, IUS, BamQC version, path
   dna={}
   rna={}

   #open the file provenance report
   with open(sw_filename) as tsv:
       #parse the report into a map
      for line in csv.DictReader(tsv, delimiter="\t"):
          ius=line["IUS SWID"]

          #choose the most recent workflow version for each IUS (library)
          #BamQC is run on DNA
          if 'BamQC' in line['Workflow Name']:
              if ius in dna:
                if dna[ius]["Workflow Version"]<line["Workflow Version"]:
                    dna[ius]={"Last Modified": line['Last Modified'], "Workflow Version": line['Workflow Version'], "File Path": line['File Path'] }
              else:
                  dna[ius]= { "Last Modified": line['Last Modified'], "Workflow Version": line['Workflow Version'], "File Path": line['File Path'] }
          else:
              #RNAseqQC is run on RNA
              if 'RNAseqQc' in line['Workflow Name']:
                  if ius in rna:
                      if rna[ius]["Workflow Version"]<line["Workflow Version"]:
                        rna[ius]={"Last Modified":    line['Last Modified'], "Workflow Version": line['Workflow Version'],"File Path": line['File Path'] }
                  else:
                      rna[ius]= {"Last Modified":    line['Last Modified'], "Workflow Version": line['Workflow Version'],"File Path": line['File Path'] }
   tsv.close()

   total_sum=0

   #Open the BamQC JSON file, pull out the total number of aligned bases
   pattern=re.compile('.*"aligned bases":(\d+).*')
   for ius in dna:
       with open(dna[ius]["File Path"]) as json:
          for line in json:
               m = pattern.match(line)
               bases=m.group(1)
               if bases is not None:
                  total_sum=total_sum+int(bases)
                  break
#               dna[ius]["aligned bases"]=m.group(1)
#               date=datetime.strptime(dna[ius]['Last Modified'],"%Y-%m-%d %H:%M:%S.%f")
       json.close()


   #Open RNAseq QC zip report, look for the summary file, pull out the total number of aligned bases
   pattern=re.compile(".*/CollectRNASeqMetricsSummary.txt")
   for ius in rna:
       with ZipFile(rna[ius]["File Path"],'r') as qczip:
           members=qczip.namelist()
           for f in filter(lambda x : pattern.match(x), members):
               with qczip.open(f) as summary:
                   for line in csv.DictReader(summary, delimiter="\t"):
                       bases=line['PF_ALIGNED_BASES']
                       total_sum=total_sum+int(bases)
                       break
               summary.close()
       qczip.close()

   #Summary stats
   print("Aligned bases:",total_sum)
   print("DNA Libraries:",len(dna))
   print("RNA Libraries:", len(rna))
       

if __name__ == "__main__":
   main(sys.argv[1:])



