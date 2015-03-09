Reformats the file provenance report and pulls in information from Pinery in order to produce reports for different OICR stakeholders.

Note: Will only work inside OICR firewalls and with a properly set up .seqware/setting file pointed at a valid SeqWare webservice with data.


GT Project Report 1

    python leeProjectReport.py --year <year> --month <month> [--use-sw-file=<seqware file provenance report> --use-pinery-file=<samples.json> --use-fastq-date]

e.g. 

    python leeProjectReport.py --use-sw-file=tmp.tsv --use-pinery-file=samples.json --year 2014 --month 11 --use-fastq-date > results.tsv
