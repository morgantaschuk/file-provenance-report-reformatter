#!/bin/bash

# counts the number of libraries produced in each month from 2012-2015

REPORT=$1

if [[ -z $REPORT ]]
then
	echo "Usage: libraries_by_month.sh report.tsv\n"
	echo "Counts the number of libraries produced in each month from 2012-2015"
	echo "using SeqWare 1.1 file provenance report"
	exit 1
fi

#set -e -o pipefail

printf "Date\tRuns\tTotal Libs\tWG Libs\tEX Libs\tTS Libs\tWT Libs\tMR Libs\n"

grep CASAVA $1 > casavas.csv

for y in {2..5}
do
#	echo "Year ${y}"
	for m in {1..12}
	do
#		echo "Month ${m}"
		#cat header.csv > tmp.csv
		date=$(printf '^201%d-%02d' "${y}" "${m}" )
#		echo "Date ${date}"
		grep "${date}" casavas.csv > tmp.csv
		cut -f14 tmp.csv|sort |uniq > libs.csv
#		echo "Found libs"

		RUNS=`cut -f19 tmp.csv|sort |uniq | wc -l`
		LIBS=`cat libs.csv| wc -l`
		WG=`grep _WG libs.csv | wc -l`
		EX=`grep _EX libs.csv | wc -l`
		TS=`grep _TS libs.csv | wc -l`
		WT=`grep _WT libs.csv | wc -l`
		MR=`grep _MR libs.csv | wc -l`

		printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "201${y}-${m}" "$RUNS" "$LIBS" "$WG" "$EX" "$TS" "$WT" "$MR"

	done	
done
rm casavas.csv
rm tmp.csv
rm libs.csv
