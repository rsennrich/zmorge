#!/usr/bin/env python
# -*- coding: utf-8 -*-
# extract state activater/deactivtor
activator =   "\s*\{\{\s*(Deutsch (.*) (Übersicht|Deklination)|Verb\-Tabelle)"
deactivator = "\s*\|?\}\}\s*" # TODO:evt sogar "\s*\}\}.*"

# extracting regexes
wordsort =  '===\s*(\{\{Wortart\|([^\|]*)\|Deutsch\}\})((,?\s*\{\{.*\}\}))*.*==='

# alternative spelling variants. Assume that spelling variatnts are links (markup: [[variant]] )
alt_spelling = "\[\[([^:\s,]*?)\]\](?!:)"

# indicates word origin
origin_native = r"(?i)deutsch|indoeuropäisch|germanisch|germ\.|\{\{gmh\.\}\}|\{\{goh\.\}\}|\{\{ie\.\}\}"
origin_classic = r"(?i)lateinisch|lat\.|griechisch"
origin_foreign = r"(?i)englisch|engl\.|französisch|franz\.|italienisch|ital\."

# link is enclosed by two square brackets; if '|' separates link from text, use only the former;
# don't allow following colon, since this indicates that link points towards some meta-information page.
link = r"\[\[([^\|\]]+?)(?:\|.*?)?\]\](?!:)"

# verbtable = '\{\{Verb\-Tabelle'
cases = "\s*\|\s*(.*)\s*=(.*)"

#remove mark-ed up information from inflection table (pronunciation help, small-font articles etc.)
case_filter = "{{.*?}}"

# find alternatives in case values e.g. 'krabbl(e)'. also could be marked as 'krabbl / krabble'
alt_parenthesis = ".*\(.+\).*"
alt_brackets = ".*\[.+\].*"