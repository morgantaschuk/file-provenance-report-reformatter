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
   adapter_seq_r1=None
   adapter_seq_r2=None
   long_opts=["use-sw-file=", "adapter-sequence-r1=", "adapter-sequence-r2="]
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
      elif opt == '--adapter-sequence-r1':
	adapter_seq_r1=arg
      elif opt == '--adapter-sequence-r2':
        adapter_seq_r2=arg
   if adapter_seq_r1 is None or adapter_seq_r2 is None or sw_filename is None:
      print("Make sure you give arguments for --use-sw-file and, --adapter-sequence-r1, and --adapter-sequence-r2.")
      sys.exit()

   # Print out header of csv file
   header = "\t".join(['Project', 'Library', 'Run', 'Lane', 'Barcode', 'Sequence', 'Percent reads trimmed'])
   print(header)

   #open the file provenance report
   with open(sw_filename) as tsv:
       #parse the report into a map
      for line in csv.DictReader(tsv, delimiter="\t"):
         annos=None
	 #find the FastQ files and calculates their adapter contamination numbers
         if 'chemical/seq-na-fastq-gzip' in line['File Meta-Type']:
             firstbit="\t".join([ line['Study Title'], line['Sample Name'], line['Sequencer Run Name'], line['Lane Number'], line['IUS Tag'] ])

             # Get Trimmed reads percentage
             filePath = line['File Path'];
             m1 = re.match(".*?_(R[1|2])_.*", os.path.basename(filePath))

             if m1 is not None:
                 firstbit = "\t".join([firstbit, m1.group(1)])
             else:
                 firstbit = firstbit + "\t"
             try:
                 if re.match(".*?_(R1)_.*", os.path.basename(filePath)) is not None:
                     process = subprocess.check_output('zcat %s | head -10000 | /oicr/local/analysis/sw/cutadapt/cutadapt-0.9.3/cutadapt -a %s -O 10 -o /dev/null -' % (filePath, adapter_seq_r1), stderr=subprocess.STDOUT, shell=True)
                 else:
                    process = subprocess.check_output('zcat %s | head -10000 | /oicr/local/analysis/sw/cutadapt/cutadapt-0.9.3/cutadapt -a %s -O 10 -o /dev/null -' % (filePath, adapter_seq_r2), stderr=subprocess.STDOUT, shell=True) 
             except subprocess.CalledProcessError as e:
                 print(" : ".join([time.strftime("%x %X"), "ERROR: Could not open file", str(e), filePath]),file=sys.stderr)
                 continue
             except IOError as e:
                 print(" : ".join([time.strftime("%x %X"), "ERROR: IOError", str(e), filePath]),file=sys.stderr)
                 continue

             m = re.findall('Trimmed\sreads.+\(\s+\d+\.\d+%\)', process)
             m2 = re.findall('\d+\.\d+%', str(m))
             line = firstbit + "\t" + m2[0]

             # Print out row of csv file
             print(line)

if __name__ == "__main__":
   main(sys.argv[1:])



