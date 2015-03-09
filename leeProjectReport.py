#!/usr/bin/python
from __future__ import print_function
import sys,getopt,time,re
from subprocess import call
import csv,zipfile,re
import urllib2
import json
import datetime

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
def usage(long_opts):
    print('annotate_fastqc.py',"[","--"+" --".join(long_opts).replace("="," <val>"),"]")
    print(' use -h to print this message')

def get_seq_samples_json_from_pinery():
    url='https://pinery.hpc.oicr.on.ca:8443/pinery/samples?type=Illumina+PE+Library+Seq'
    try:
        sample_str = urllib2.urlopen(url)
    except urllib2.HTTPError, e:
        print("HTTP error: %d" % e.code)
        sys.exit(e.code)
    except urllib2.URLError, e:
        print("Network error: %s" % e.reason.args[1])
        sys.exit(2)
    return sample_str

def get_sample_dict(sample_str):
    samples=json.load(sample_str)
    sample_dict={}
    for s in samples:
        library=s['name']
        date=parse_pi_date(s['created_date'])
        project=s['project_name']
        if (library not in sample_dict):
            sample_dict[library]=dict(library=library,created=[date],project=project)
        else:
            sample_dict[library]['created'].append(date)

    return sample_dict

def get_attribute(full_atts, att):
    m = re.findall(att+'[\.0-9]*=([\w\s]+);?', full_atts)
    return set(m)

def get_basename(library_name):
    m2 = re.search("^[A-Z]{2,6}_[0-9]{4}", library_name)
    if (m2 is not None):
        return m2.group(0)
    else:
        return "N/A"

def main(argv):
    reportarg = []
    sw_filename=None
    pi_file=None
    title="annot"
    test=False
    year=None
    month=None

    long_opts=["test","study-name=","root-sample-name=","sample-name=","sequencer-run-name=","ius-SWID=","lane-SWID=","use-sw-file=", "use-pinery-file=", "year=", "month="]
    try:
    	opts, args = getopt.getopt(argv,"h",long_opts)
    except getopt.GetoptError:
    	usage(long_opts)
    	sys.exit(2)
    
    for opt, arg in opts:
    	if opt == '-h':
    	    usage(long_opts)
            sys.exit()
	elif opt == '--test':
	    test=True
	elif opt == '--use-sw-file':
	    sw_filename=arg
        elif opt == '--use-pinery-file':
            pi_file=open(arg)
        elif opt == '--year':
            year=int(arg)
        elif opt == '--month':
            month=int(arg)
	else:
	    reportarg.append(opt)
	    reportarg.append(arg)

    if year is None or month is None:
        print("Please specify --year and --month")
        sys.exit(2)

    if sw_filename is None:
	#generate the report
    	sw_filename="tmp.tsv"
	mycall = ["seqware", "files", "report", "--out", sw_filename];
	mycall.extend(reportarg)
	call(mycall)
    if pi_file is None:
        pi_file=get_seq_samples_json_from_pinery()

    #seq libraries > [created_dates]
    pi_s=get_sample_dict(pi_file)

    #fq libraries > [sequencer runs], project, donor


    #open the file provenance report
    with open(sw_filename) as tsv:
        sw_s={}
	#parse the report into a map
	for line in csv.DictReader(tsv, delimiter="\t"):
            filetype=line['File Meta-Type']
            if ("chemical/seq-na-fastq-gzip" != filetype):
                continue
            fqdate=parse_sw_date(line['Last Modified'])
            library=line['Sample Name']
            sr=line['Sequencer Run Name']
            project=line['Study Title']
            donor=line['Root Sample Name']
            if (library not in sw_s):
		sw_s[library]=dict(sr=[sr], library=library, project=project, donor=donor, fqdate=[fqdate])
            else:
                sw_s[library]['sr'].append(sr)
                sw_s[library]['fqdate'].append(fqdate)

    final_dict={}
    for libkey, datvalues in sw_s.iteritems():
        fastq=str(float(len(datvalues['sr'])/2))
        srst=",".join(datvalues['sr'])
        final_dict[libkey]={'Project':datvalues['project'], 'Donor':datvalues['donor'], 'Library':datvalues['library'], "Sequencer runs":srst, "Libraries with FASTQ":fastq, 'FASTQs created':datvalues['fqdate']}
        final_dict[libkey]['Libraries in LIMS']="0"
        final_dict[libkey]['Libraries created']=[]
        
    for libkey, datvalues in pi_s.iteritems():
        library=datvalues['library']
        if (library not in final_dict):
            final_dict[libkey]={'Project':datvalues['project'], 'Donor':get_basename(library), 'Library':library, 
                'Libraries created':datvalues['created'], 'Libraries in LIMS':str(len(datvalues['created']))}
            final_dict[libkey]['Libraries with FASTQ']="0"
            final_dict[libkey]['Sequencer runs']="N/A"
            final_dict[libkey]['FASTQs created']=[]
        else:
            final_dict[libkey]['Libraries in LIMS']=str(len(datvalues['created']))
            final_dict[libkey]['Libraries created']=datvalues['created']


    header=['Project','Donor', 'Library', 'Sequencer runs', 'Libraries in LIMS', 'Libraries with FASTQ', 'Libraries created', 'FASTQs created']
    print("\t".join(header))


    for row in final_dict.values():
        printrow=[]
        if (check_date(row['Libraries created'],year,month)):
            for n in header[0:6]:
                printrow.append(row[n])
            printrow.append(",".join([str(x) for x in row['Libraries created']]))
            printrow.append(",".join([str(x) for x in row['FASTQs created']]))
            print("\t".join(printrow))


def parse_pi_date(date):
    """
    Python really doesn't like Pinery's timestamps with timezones so I'm slicing them off
    e.g. '2013-04-24T16:40:28-04:00
    """
    realdate=datetime.datetime.strptime(date[0:date.rfind("-")], "%Y-%m-%dT%H:%M:%S") 
    return realdate

def parse_sw_date(date):
    """
    Removing microseconds because why not.
    e.g. 2014-01-31 23:09:57.228381
    """
    realdate=datetime.datetime.strptime(date[0:date.rfind(".")],"%Y-%m-%d %H:%M:%S")
    return realdate

def check_date(list_dates, year, month):
    """
    All dates in ISO format now
    e.g. 2013-04-24T16:40:28
    """
    if list_dates == "N/A":
        return False
    for date in list_dates:
        if (date.year==year and date.month==month):
            return True
    return False


	#mycall = ["qsub", "-l", "h_vmem=8G", "-N", title,"-cwd", "-b", "y", '"bash '+title+'"']

	#if not test:
#		call(mycall)
	#else:
	#print(" ".join(mycall))

if __name__ == "__main__":
    main(sys.argv[1:])
