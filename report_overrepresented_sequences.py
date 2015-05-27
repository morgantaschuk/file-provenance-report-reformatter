#!/oicr/local/sw/Python-2.7.2/bin/python2.7
from __future__ import print_function

import sys,getopt,time
import subprocess
import csv,re
import os
import gzip

def usage(long_opts):
   print('report_overrepresented_sequences.py',"[","--"+" --".join(long_opts).replace("="," <val>"),"]")
   print('   use -h to print this message')

def main(argv):
   sw_filename=None
   adapter_seq=None
   long_opts=["use-sw-file=", "adapter-sequence="]
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
      elif opt == '--adapter-sequence':
	adapter_seq=arg
   if adapter_seq is None or sw_filename is None:
      print("Make sure you give arguments for --use-sw-file and --adapter-sequence.")
      sys.exit()

   # Make csv file to write to
   csvFile = open('AdapterContamination.csv','w')
   header = ",".join(['Project', 'Library', 'Run', 'Lane', 'Barcode', 'Sequence', 'Percentage'])
   csvFile.write(header + "\n")

   #open the file provenance report
   with gzip.open(sw_filename) as tsv:
       #parse the report into a map
      for line in csv.DictReader(tsv, delimiter="\t"):
         annos=None
	 #find the FastQ files and calculates their adapter contamination numbers
         if 'chemical/seq-na-fastq-gzip' in line['File Meta-Type']:
             firstbit=",".join([ line['Study Title'], line['Sample Name'], line['Sequencer Run Name'], line['Lane Number'], line['IUS Tag'] ])
             # Get Trimmed reads percentage
             filePath = line['File Path'];
             m1 = re.match(".*?_(R[1|2])_.*", os.path.basename(filePath))
             if m1 is not None:
                 firstbit = ",".join([firstbit, m1.group(1)])
             else:
                 firstbit = firstbit + ","
             p1 = subprocess.Popen(["zcat", filePath], stdout=subprocess.PIPE)
             p2 = subprocess.Popen(["head", "-100000"], stdin=p1.stdout, stdout=subprocess.PIPE)
             p1.stdout.close()
             p3 = subprocess.check_output("/oicr/local/analysis/sw/cutadapt/cutadapt-0.9.3/cutadapt -a %s -O 10 -o /dev/null -" % (adapter_seq), stderr=subprocess.STDOUT, stdin=p2.stdout, shell=True)
             p2.stdout.close()
             m = re.findall('\(\s+\d+\.\d+%\)', p3)
             m2 = re.findall('\d+\.\d+%', str(m))

             # Write to csv file
             line = firstbit + "," + m2[0]
             csvFile.write(line + "\n")
   csvFile.close()

if __name__ == "__main__":
   main(sys.argv[1:])



