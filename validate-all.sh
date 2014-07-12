#!/bin/bash
set -e
SRCPATH="${0%/*}"
[ "$SRCPATH" != "$0" ] || SRCPATH=.
SCRIPT="$SRCPATH/schema-matching.py"
[ -n "$PYTHON" ] || PYTHON="`read -r cmd < "$SCRIPT" && [ "${cmd:0:2}" = '#!' ] && cmd="${cmd:2}" && echo "${cmd%% *}" || command -v python`"

ACTION=schema_matching
case "$1" in
	--benchmark)
		ACTION="${1:2}"
		shift;;
	--)
		shift;;
	--*)
		echo "Invalid option: $1" >&2
		exit 2;;
esac

declare -a DESCRIPTIONS
case "$1" in
	*.py) DESCRIPTIONS=("`readlink -f -- "$1"`"); shift;;
esac

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

schema_matching() {
	rv=0
	for in1 in "$@"; do
		for in2 in "$@"; do
			if [ "$in1" \< "$in2" ]; then
				echocmd $PYTHON "$SCRIPT" --validate "$in1" "$in2" "${DESCRIPTIONS[@]}" || rv=1
				echo
			fi
		done
	done
	return $rv
}

benchmark() {
	set -o pipefail
	schema_matching "$@" 2>&1 |
	awk '
		BEGIN{ all=0; errors=0; }
		{
			print;
			if (/^found [0-9]+ => [0-9]+, expected [0-9]+ => [0-9]+/)
				all+=1
			if (/^[0-9]+ invalid, [0-9]+ impossible, and [0-9]+ missing matches/) {
				all+=$6; errors+=$1+$6;
			}
		}
		END{
			fflush("/dev/stdout");
			close("/dev/stdout");
			printf("%d errors out of %d possible matches (%.0f %%)\n", errors, all, errors / all * 100) > "/dev/stderr";
		}' \
			3>&- 3>&1 1>&2 2>&3
}


$ACTION "$@"
