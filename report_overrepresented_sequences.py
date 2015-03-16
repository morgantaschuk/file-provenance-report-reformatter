#!/usr/bin/python
from __future__ import print_function

import sys,getopt,time
from subprocess import call
import csv,zipfile,re

def usage(long_opts):
   print('report_overrepresented_sequences.py',"[","--"+" --".join(long_opts).replace("="," <val>"),"]")
   print('   use -h to print this message')

def open_fastqc(fastqc_zip,match_string,firstbit):
    """ 
    Open the fastqc zip, find the fastqc_data.txt and pull out the matches as specified in match_strings.
    """
    annotations=False
    #open the fastqc zip
    try:
        match_string=">>Overrepresented sequences"

        with zipfile.ZipFile(fastqc_zip,'r') as myzip:
            matching = filter(lambda element: "fastqc_data.txt" in element, myzip.namelist())
            iterator=iter(myzip.read(matching[0],'rU').split("\n"))
            for line in iterator:
                if line.startswith(match_string):
                    line = iterator.next()
                    while not line.startswith(">"):
                        if not line.startswith("#"):
                            print(firstbit+"\t"+line)
                        line = iterator.next()
                    annotations=True
                    break
        if annotations==False:
            print(firstbit+"\tN/A")
    except zipfile.BadZipfile as e:
        print(" : ".join([time.strftime("%x %X"), "ERROR: BadZipfile", str(e), fastqc_zip]),file=sys.stderr)
    except IOError as e:
        print(" : ".join([time.strftime("%x %X"), "ERROR: IOError", str(e), fastqc_zip]),file=sys.stderr)

def main(argv):
   reportarg = []
   test=False
   sw_filename=None
   long_opts=["test","study-name=","root-sample-name=","sample-name=","sequencer-run-name=","ius-SWID=","lane-SWID=","use-sw-file="]
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
      elif opt == '--test':
         test=True
      else:
         reportarg.append(opt)
	 reportarg.append(arg)
         title="_".join([title,arg])


   if sw_filename is None:
        #generate the report
        sw_filename="tmp.tsv"
        mycall = ["seqware", "files", "report", "--out", sw_filename];
        mycall.extend(reportarg)
        call(mycall)


   #The strings to match for the FastQC reports
   #match_strings=["^(Encoding)[\s]*(.*)","^(Total Sequences)[\s]*(.*)","^(Sequence length)[\s]*(.*)","^(%GC)[\s]*(.*)"]
   match_string="Overrepresented sequences"

   #open the file provenance report
   with open(sw_filename) as tsv:
      print("\t".join(['Project', 'Identity', 'Library', 'Run', 'Lane', 'Barcode', 'Sequence', 'Count', 'Percentage', 'Possible Source']))
       #parse the report into a map
      for line in csv.DictReader(tsv, delimiter="\t"):
         annos=None
	 #find the FastQC workflow reports and pull out the annotation lines
         if line['Workflow Name'] == 'FastQC' and line['File Meta-Type'] == 'application/zip-report-bundle':
            firstbit="\t".join([ line['Study Title'], line['Root Sample Name'], line['Sample Name'], line['Sequencer Run Name'], line['Lane Number'], line['IUS Tag'] ])
            open_fastqc(line['File Path'],match_string,firstbit)


if __name__ == "__main__":
   main(sys.argv[1:])



