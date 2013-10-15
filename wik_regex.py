#!/usr/bin/env python
# -*- coding: utf-8 -*-
# extract state activater/deactivtor
activator =   "\{\{(Deutsch (.*) (Übersicht|Deklination)|Verb\-Tabelle)"
deactivator = "\s*\}\}\s*" # TODO:evt sogar "\s*\}\}.*"

# extracting regexes
word = '\s*<title>(.*)</title>\s*'
wordsort =  '===\s*(\{\{Wortart\|([^\|]*)\|Deutsch\}\})((,?\s*\{\{.*\}\}))*\s*==='
# verbtable = '\{\{Verb\-Tabelle'
cases = "\|(.*)=(.*)"

# find alternatives in case values e.g. 'krabbl(e)'. also could be marked as 'krabbl / krabble'
alt_parenthesis = ".*\(.+\).*"
