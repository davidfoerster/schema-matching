#!/bin/sh
set -eu
cd "${0%/*}/data" 2>&- || cd data
exec ../../schema-matching --validate --field-delimiter=';' *.csv
