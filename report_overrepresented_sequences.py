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

    #open the fastqc zip
    try:
        match_string=">>Overrepresented sequences"
        m=re.match(".*?_(R[1|2])_.*",fastqc_zip)
        if m is not None:
            firstbit="\t".join([firstbit, m.group(1)])
        else:
            firstbit=firstbit+"\t "
        with zipfile.ZipFile(fastqc_zip,'r') as myzip:
            matching = filter(lambda element: "fastqc_data.txt" in element, myzip.namelist())
            iterator=iter(myzip.read(matching[0],'rU').split("\n"))
            doathing(iterator,match_string,firstbit)
    except zipfile.BadZipfile as e:
        print(" : ".join([time.strftime("%x %X"), "ERROR: BadZipfile", str(e), fastqc_zip]),file=sys.stderr)
    except IOError as e:
        print(" : ".join([time.strftime("%x %X"), "ERROR: IOError", str(e), fastqc_zip]),file=sys.stderr)

def doathing(iterator,match_string,firstbit):
    annotations=False    
    for line in iterator:
        if line.startswith(match_string):
            line = iterator.next()
            percent=0.0
            source=[]
            while not line.startswith(">"):
                if not line.startswith("#"):
                    report=line.split("\t")
                    lineper=float(report[2])
                    linesou=report[3]
                    if "Adapter" in linesou:
                        matstr="(.+?)[,|(]"
                        m=re.match(matstr,linesou)
                        if m is not None:
                            linesou=m.group(1)
                            percent=percent+lineper
                            source.append(linesou)
                line = iterator.next()
            if source:
                annotations=True
                print("\t".join([firstbit, str(percent), ",".join(set(source))]))
                break
            #if annotations is not True:
            #    print(firstbit+"\tN/A")

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
      print("\t".join(['Project', 'Library', 'Run', 'Lane', 'Barcode', 'Sequence', 'Count', 'Percentage', 'Possible Source']))
       #parse the report into a map
      for line in csv.DictReader(tsv, delimiter="\t"):
         annos=None
	 #find the FastQC workflow reports and pull out the annotation lines
         if line['Workflow Name'] == 'FastQC' and line['File Meta-Type'] == 'application/zip-report-bundle':
            firstbit="\t".join([ line['Study Title'], line['Sample Name'], line['Sequencer Run Name'], line['Lane Number'], line['IUS Tag'] ])
            open_fastqc(line['File Path'],match_string,firstbit)


if __name__ == "__main__":
   main(sys.argv[1:])



