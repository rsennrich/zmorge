#!/usr/bin/env python
# -*- coding: utf-8 -*-
# this is a simple test file for testing regexes.
# the dict keys are the regexes
# the dict values are for each key a list with two lists in it
#   the first list:     consists of strings that should be matches
#   the second list:    consists of strings that should NOT be matched
#
# TODO: extend test with assumed match results
from __future__ import unicode_literals, print_function
import re
import wik_regex

regex_test_dict = dict()

regex_test_dict[wik_regex.wordsort] = [
    # should match these 
    [
        "===  {{Wortart|Substantiv|Deutsch}} ===",
        "===  {{Wortart|Substantiv|Deutsch}}, {{f}} ===",
        "=== {{Wortart|Substantiv|Deutsch}}, {{m}} ===" # found for entry 'Auflauf'
    ],
    # should not match these
    [
    ]
]

# TODO: write simple test routine that iterates over test hash

for regex_uncompiled, testlists in regex_test_dict.items():
		print("##### test regex '" + regex_uncompiled + "'")
		positiv_tests = testlists[0] # these should match
		negativ_tests = testlists[1] # these should NOT match
		regex = re.compile(regex_uncompiled)
		print("## test positiv tests (these should be matched!)")
		for ptest in positiv_tests:
				match = regex.match(ptest)
				if match == None:
						print("Regex did not match: '" + ptest + "'")
				else:
						print("did match, groups are: " + str(match.groups()))
		print("## test negativ tests (these should NOT be matched!)")
		for ntest in negativ_tests:
				match = regex.match(ntest)
				if match != None:
						print("Regex matched: '" + ntest + "'")
