#!/bin/sh -e
cd "${0%/*}/data" 2>&- || cd data
exec ../../schema-matching --compare-descriptions --desc :collector.description.normal.L2 --field-delimiter=';' *.csv
