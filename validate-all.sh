#!/bin/bash
set -e
SRCPATH="${0%/*}"
[ "$SRCPATH" != "$0" ] || SRCPATH=.

if [[ "$1" == *.p ]]; then
	WEIGHTS="$1"
	shift
fi

if [ $# -eq 0 ]; then
  [ "$PWD" -ef "$SRCPATH" ] || cd "$SRCPATH"
	set -- input-data/*.csv
fi


echocmd() {
  local -i rv=0
  local cmd="$1"
  shift

  echo "${cmd##*/}" "$*:"
  "$cmd" "$@" || rv=$?
  echo "${cmd##*/}" "$*: exit code" $rv
  return $rv
 }

schema-matching() {
	echocmd "$SRCPATH/schema-matching.py" "$1" "$2" --validate $WEIGHTS
}

rv=0
for in1 in "$@"; do
	for in2 in "$@"; do
		if [ "$in1" \< "$in2" ]; then
			schema-matching "$in1" "$in2" || rv=1
			echo
		fi
	done
done
exit $rv
