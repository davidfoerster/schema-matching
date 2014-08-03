#!/bin/sh -e
cd "${0%/*}/data" 2>&- || cd data
exec ../../schema-matching --match --field-delimiter=';' -vv abc.csv horst.csv
