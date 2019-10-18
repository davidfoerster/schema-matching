#!/bin/sh
set -eu
cd "${0%/*}/data" 2>&- || cd data
exec ../../schema-matching --match --field-delimiter=';' -v abc.csv horst.csv "$@"
