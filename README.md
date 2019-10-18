# Schema Matching

Match schema attributes by value similarity.


## Usage

Run `./schema-matching --help` to see a usage description.


### Examples

See the shell scripts in `demo`. I suggest that you start with `1-match.sh` for
something simple. The output will be, in this order,

 1. the norms between each column pair, i. e. a measure of how different they
    are, between 0 (identical) and 1 (completely different),

 2. the norm of the most closely matching column mapping, and

 3. the most closely matching column mapping, one pair per line.

1\. and 2. require at least one level of verbosity (using `-v` or `--verbose`).


## Pre-requisites

 - **Python 3** (tested with v3.6.8)
