#!/bin/bash

#set -e -o pipefail

export PERL5LIB=/oicr/local/analysis/lib/perl/pipe/lib/perl5
export JVM_OPTS=-Xmx500M
module load python
module load java/1.7.0_72

export JVM_OPTS=-Xmx200M
export fpr_d=`date +%Y%m%d`
export all_name="${1}_overrepresented_sequences.tsv"
export directory="OverrepresentedSequences"

/oicr/local/sw/Python-2.7.2/bin/python2.7 report_overrepresented_sequences.py --use-sw-file "${fpr_d}_${1}_tmp-report.tsv" --adapter-sequence-r1 AGATCGGAAGAGCACACGTCTGAACTCCAGTCACACGCTCGAATCTCGTA --adapter-sequence-r2 AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT > "${all_name}"

for i in `tail -n +2 "${all_name}" | cut -f1 | sort | uniq`
do
	cat ${all_name} | awk -v project=$i -F $'\t' 'BEGIN {OFS = FS} { if (project == $1) print $0;}' >> "${i}_overrepresented_sequences.tsv"
	#grep ${i} ${all_name} >> "${i}_overrepresented_sequences.tsv"
done

rm "${all_name}"
rm "${fpr_d}_${1}_tmp-report.tsv"
