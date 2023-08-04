#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from __future__ import unicode_literals, print_function
import re
import fileinput 
import time
from collections import defaultdict
from datetime import datetime
from random import sample
import config
import multiprocessing 
import sys
import copy
import json
import codecs

try:
    from lxml import etree as ET
except ImportError:
    from xml.etree import cElementTree as ET

from xml.sax.saxutils import escape
from fst_wrapper import FstWrapper # interactive interface to finite-state morphology for inflection prediction
import wik_regex    # collection of regexes used
import config

########## TODO / TODOs
# - Logger einfügen (elegant durch print ersetzung!)
#   à la:
#    import logging
#    logging.basicConfig(filename='example.log',level=logging.DEBUG)
#    logging.debug('This message should go to the log file')
#    logging.info('So should this')
#    logging.warning('And this, too')

# NOTE: debug_lvl can be adjusted in wiktionary_debug_lvl.py

print(("Debug is " + ( "ON (level: " + str(config.debug_lvl) + ")"  if config.debug_lvl > 0 else "OFF" )))

workers = [] # NOTE: one global variable ... isnt that ugly ?

# NOTE: this function is from a forum http://mail.python.org/pipermail/tutor/2009-October/072483.html
def mapToDict(d):
    """recursively convert defaultdicts into regular dicts"""
    d = dict(d)
    d.update((k, mapToDict(v)) for k,v in list(d.items()) if isinstance(v, defaultdict))
    return d

# returns all indices of occurrences of substring sword in string t
def findWordIndices(t, word_indeces, sword):
    # print(t, word_indeces)
    ind = t.find(sword)
    if ind != -1:
        try:
            word_indeces.append((ind+wortart_indeces[-1]+len(sword)))
        except:
            word_indeces.append(ind)
        word_indeces = findWaInd(t[(ind+len(sword)):], word_indeces, sword)
    return word_indeces


def extractFromWikidump(wikidump_filepath):

    # if the wiki version changes, check for differences before updating this value
    wiki_version = "{http://www.mediawiki.org/xml/export-0.10/}"

    print(("reading file '" + wikidump_filepath + "'"))
    ######## preparing data structure
    ## structure: wordsort > word > cases > case > value
    ##                            > wordsort additional informational
    words = defaultdict(list)


    ######## preparing regexes
    extract_state = False
    # extract state de- & activator regexes
    extract_state_activator =   re.compile(wik_regex.activator)
    extract_state_deactivator = re.compile(wik_regex.deactivator)
    # extractor regex
    extractor_wordsort =    re.compile(wik_regex.wordsort)
    extractor_alt_spelling = re.compile(wik_regex.alt_spelling)
    extractor_native = re.compile(wik_regex.origin_native)
    extractor_classic = re.compile(wik_regex.origin_classic)
    extractor_foreign = re.compile(wik_regex.origin_foreign)
    extractor_link = re.compile(wik_regex.link)
    # extractor_verbtable =        re.compile(wik_regex.verbtable)
    extractor_cases =       re.compile(wik_regex.cases)
    extractor_case_filter = re.compile(wik_regex.case_filter)

    # filters after base-extraction
    filter_non_linguistic_case = re.compile("(?i)\s*(Bild|Weitere_|Hilfsverb|keine weiteren|Befehl_du|Passiv|Genus)") # TODO: move to wik_regex

    # values that indicate no entry
    blacklist = set(["—", "–", "?", "-"])

    # variables for context information
    last_word = None
    last_wordsort = None
    last_wordsort_additional_info = None
    # reads file line by line without keeping the already read lines in memory
    count_alternatives = 0

    for event, elem in ET.iterparse(wikidump_filepath):
        if elem.tag != wiki_version+'page':
            continue

        title = elem.find('./' + wiki_version + 'title')
        if title is None:
            elem.clear()
            continue
        word = title.text

        # skip multi-word pages
        if not word or " " in word or "-" in word or ":" in word:
            elem.clear()
            continue

        text_element = elem.find('.//' + wiki_version + 'text')
        if text_element is None or text_element.text is None:
            elem.clear()
            continue

        i = 0
        wordsort = None
        wordsort_additional_info = None
        extract_state = False
        entry = defaultdict(dict)
        entry['lemma'] = word

        text = text_element.text.splitlines()

        german = False

        for line in text:
            i += 1

            # new entry
            if line.startswith('== ') and line.endswith(' =='):
                if 'Sprache|Deutsch' in line:
                    german = True
                else:
                    german = False
                if len(entry) > 1 and wordsort:
                    words[wordsort].append(entry)
                entry = defaultdict(dict)
                entry['lemma'] = word

            if not german:
                continue

            # extract spelling variations
            if ('{{Alternative Schreibweisen}}' in line or '{{Alte Rechtschreibung}}' in line or '{{Veraltete Schreibweisen}}' in line) and i < len(text):
                alt_spellings = set(extractor_alt_spelling.findall(text[i]))
                alt_spellings.difference_update(set(['Schweiz', 'Österreich', 'Liechtenstein', 'Deutschland'])) # names of regions where spelling variation occurs are sometimes extracted by accident
                if 'alt_spelling' in entry:
                    entry['alt_spelling'].update(alt_spellings)
                else:
                    entry['alt_spelling'] = alt_spellings
                continue

            # extract origin
            if '{{Herkunft}}' in line and not 'origin' in entry:

                # find end of origin text block
                for j in range(i, len(text)):
                    if text[j].startswith('{{'):
                        break
                origin_text = '\n'.join(text[i:j])

                # word may have multiple origins; we prioritize 'nativ', then 'klassisch'; default if no match is 'nativ'
                if extractor_native.search(origin_text):
                    entry['origin'] = 'nativ'
                elif extractor_classic.search(origin_text):
                    entry['origin'] = 'klassisch'
                elif extractor_foreign.search(origin_text):
                    entry['origin'] = 'fremd'

            # extract origin
            if '{{Bedeutungen}}' in line:

                # find end of origin text block
                for j in range(i, len(text)):
                    if text[j].startswith('{{'):
                        break
                meaning_text = '\n'.join(text[i:j])

                if wordsort == 'Abkürzung' and not 'meaning' in entry:
                    # word may have multiple origins; we prioritize 'nativ', then 'klassisch'; default if no match is 'nativ'
                    link = extractor_link.search(meaning_text)
                    if link:
                        entry['meaning'] = link.groups()[0]

                # gender of first names is inconsistently annotated (sometimes like for other nouns; sometimes only in 'Bedeutung' text)
                if entry['info'] and 'Vorname' in entry['info']:
                    if 'weiblicher Vorname' in meaning_text or 'weiblicher [[Vorname]]' in meaning_text:
                        entry['info'] += " {{f}}"
                    if 'männlicher Vorname' in meaning_text or 'männlicher [[Vorname]]' in meaning_text:
                        entry['info'] += " {{m}}"

            if not extract_state:
                try:
                    new_wordsort = extractor_wordsort.match(line).group(2)
                    wordsort_additional_info = extractor_wordsort.match(line).group(3)
                    if wordsort:
                        words[wordsort].append(entry)
                        entry = defaultdict(dict)
                        entry['lemma'] = word
                    wordsort = new_wordsort
                    entry['info'] = wordsort_additional_info
                except:
                    pass
                matches = extract_state_activator.match(line)
                if matches and wordsort:
                    if config.debug_lvl > 0: print("############ Try to extract for:", last_word, last_wordsort, matches.groups())
                    extract_state = True
            elif extract_state:
                # first check if we are still in the zone of interest
                finished = extract_state_deactivator.match(line)
                if finished:
                    if config.debug_lvl > 0: print("############### stop extraction gracefully here")
                    extract_state = False
                    continue
                # now let's extract
                try:
                    case, word_in_case = extractor_cases.match(line).groups()
                    if config.debug_lvl > 0: print("## extraction: ", last_word, ":", case, "=>", word_in_case)
                    # cleanup
                    if '}}' in word_in_case and not '{{' in word_in_case: #inflection table ending without newline
                        word_in_case = word_in_case.split('}}')[0]
                        extract_state = False
                    if word_in_case in blacklist:
                        continue
                    word_in_case = extractor_case_filter.sub('',word_in_case)
                    if filter_non_linguistic_case.match(case):
                        if config.debug_lvl > 0: print("Found non-linguistic case. dont add it ") 
                        continue
                    word_in_case = word_in_case.strip()
                    if word_in_case:
                        # new formatting for alternativ forms:
                        # "Singular Genitiv*" -> map to old formatting, which is then split again down the line
                        if case.endswith('*'):
                            case = case.strip('*')
                            if case in entry["cases"]:
                                entry["cases"][case] += '<br />' + word_in_case
                            else:
                                entry["cases"][case] = word_in_case
                        else:
                            entry["cases"][case] = word_in_case
                except:
                    if config.debug_lvl > 0: print("EXCEPTION. jump to next line") # TODO: better handling ?
                    if config.debug_lvl > 0: print(("=> could not parse line: " + line))
                    continue
        if wordsort:
            words[wordsort].append(entry)

        elem.clear()
    return words


# convert sets into lists for JSON serialization
class MyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

def dumpJSON(words, filename=None):
    #if config.debug_lvl == 0:
    print("dump into json file (this could take a while)")
    if filename == None:
        filename = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + "_wikiwords" + ".json"
    if sys.version_info < (3, 0):
        outfile = codecs.open(filename, 'w', encoding='UTF-8')
    else:
        outfile = open(filename,'w', encoding='UTF-8')
    json.dump(words, outfile, indent=2, ensure_ascii=False, cls=MyJSONEncoder)

# any json can be loaded with this function
def loadJSON(filePath):
    if sys.version_info < (3, 0):
        stream = codecs.open(filePath, 'r', encoding='UTF-8')
    else:
        stream = open(filePath, 'r', encoding='UTF-8')
    return json.load(stream)

# this function maps collected informations from wiktionary to smor features
# e.g. if some case with 'Akkusativ' is available => the smor feature <Acc> should be saved
# e.g. plural => <Pl> 
# NOTE: also the pos tag is examined in here
# NOTE: this smor features can then be used to filter the generated possible Analysis in 'fst_wrapper.py'
def extractSmorFeatures(words):
    # first prepare all regexes on different levels
    # TODO: this can be done before ...
    # NOTE: the keys are REGEXs, the values are the connected smor-feature if the match is positiv
    # NOTE: feature are used to filter generated analysis
    wordsort_features = {
        "Adjektiv"  : "<+ADJ>",
        "Adverb"    : "<+ADV>",
        "Artikel"   : "<+ART>",
        "Verb"      : "<+V>",
        "Präposition"  : "<+PREP>",
        "Konjunktion"  : "<+CONJ>",
        "Substantiv"  : "<+NN>", 
        "V"      : "<+V>",
        "NN"      : "<+NN>",
        "ADV"    : "<+ADV>",
    }

    gender_features = {
        "m" : "<Masc>",
        "f" : "<Fem>",
        "n" : "<Neut>",
        "ohne feststehendes Genus" : "<NoGend>"
    }
    wordcase_features = {
        "Akkusativ" : "<Acc>",
        "Nominativ" : "<Nom>",
        "Genitiv"   : "<Gen>",
        "Dativ"     : "<Dat>",
        "Singular"  : "<Sg>", 
        "Plural"    : "<Pl>",
        "Positiv"   : "<Pos>", 
        "Komparativ": "<Comp>", 
        "Superlativ": "<Sup>", 
        "Gegenwart" : "<Pres>",
        "Vergangenheit": "<Past>",
        "_ich": "<1>",
        "_er": "<3>",
        "Gegenwart_du": "<2>",
        "Gegenwart_ihr": "<2>",
        "Befehl_ihr": "<Imp><Pl>",
        "schwach": "<Wk>", 
        "stark": "<St>", 
#        "gemischt": "...", # TODO
        "Indikativ": "<Ind>",
        "Konjunktiv II": "<Past><Subj>",
        "Partizip II": "<PPast>",
    }
    wordsort_pos = {
        "Adjektiv"                  : "ADJ",
        "Abkürzung"                 : "ABBR",
        "Verb"                      : "V",
        "Hilfsverb"                 : "V",
        "Präposition"               : "OTHER",
        "Konjunktion"               : "OTHER",
        "Substantiv"                : "NN",
        "Vorname"                   : "NN", # changed to NPROP later
        "Nachname"                  : "NN",
        "Eigenname"                 : "NN",
        "Toponym"                   : "NN",
        "Adverb"                    : "ADV",
        "Modaladverb"               : "ADV",
        "Fokuspartikel"             : "ADV",
        "Gradpartikel"              : "ADV",
        "Interrogativadverb"        : "ADV",
        "Konjunktionaladverb"       : "ADV",
        "Lokaladverb"               : "ADV",
        "Pronominaladverb"          : "ADV",
        "Temporaladverb"            : "ADV",
        "Subjunktion"               : "OTHER",
        "Vergleichspartikel"        : "OTHER",
        "Interjektion"              : "OTHER",
        "Grußwort"                  : "OTHER",
        "Grußformel"                : "OTHER",
        "Onomatopoetikum"           : "OTHER",
        "Antwortpartikel"           : "OTHER",
        "Negationspartikel"         : "OTHER"
    }

    # compile regexes
    for feature_lvl in [wordsort_features, gender_features, wordcase_features]:
        for key, value in list(feature_lvl.items()):
            feature_lvl[re.compile(".*" + key + ".*")] = value # TODO: dangerous compile? 
            del(feature_lvl[key]) # delete old entry

    
    # now let's do the big work
    for wordsort, wds in list(words.items()):
        # at this level extract wordsort specific features e.g. pos-class, stem
        # this info will added below to each of the words of this wordsort
        wordsort_smor_features = []
        pos = None
        # get the POS (part of speech) information for free
        if wordsort in list(wordsort_pos.keys()):
            pos = wordsort_pos[wordsort] 
        for feature_regex, feature in list(wordsort_features.items()):
            if feature_regex.match(wordsort) != None or feature_regex.match((pos or '')) != None:            
                if config.debug_lvl > 0: print("Matched wordsort => add feature: " + feature)
                wordsort_smor_features.append(feature)

        for info in wds:

            if not info:
                continue

            # at this level extract word specific features e.g. gender for nouns
            word_smor_features = []
            for feature_regex, feature in list(gender_features.items()):
                if info.get('gender') and feature_regex.match(info['gender']):
                    word_smor_features.append(feature)

            # prepare smor features dict
            info["smor_features"] = defaultdict(list)
            for case, case_value in list(info['cases'].items()):
                # at this level extract wordcase specific features e.g. case (nominatic, accustativ), time ...
                wordcase_smor_features = []
                for feature_regex, feature in list(wordcase_features.items()):
                    if feature_regex.match(case) != None:            
                        wordcase_smor_features.append(feature)

                # finally combine the features from all levels 
                info["smor_features"][case] = wordsort_smor_features + word_smor_features + wordcase_smor_features
            # save pos
            info["pos"] = pos

            if pos == "V":
                info["stem"] = getVerbStem(info["lemma"])
            else:
                info["stem"] = info["lemma"]
    return words

def getVerbStem(verb):
    if verb[-2:] == 'en':
        return verb[:-2]
    elif verb[-3:] == 'ern' or verb[-3:] == 'eln':
        return verb[:-1] 
    else:
        if config.debug_lvl > 0: print(("!!!! COULD NOT determine verbstem of '" + verb + "'"))
        return verb

# just an info function
# prints wordsorts and number of words for each
def wordStats(words):
    print("#### wordsort and count each")
    for k,v in list(words.items()):
        print(k, "=>" , len(v))

# just an info function
def extractPossibleCases(words):
    all_cases = set()
    for wordsort, wds in list(words.items()):
        for word, info in list(wds.items()):
            for case in list(info['cases'].keys()):
                all_cases.add(case)
    return all_cases

# cleans casevalues AND finds possible alternatives
# NOTE: after this function every casevalue is a list of strings (even if there is only one string)
def cleanCasesAndSplit(words):
    # ######### here we define cleanup regexes (in the values) for wordsorts

    regex_alt_parenthesis = re.compile(wik_regex.alt_parenthesis)
    regex_alt_brackets = re.compile(wik_regex.alt_brackets)

    # <br>, </br>, <br />, <br/>
    regex_pagebreak = re.compile("\s*</?br\s*/?>\s*")

    # for each wordsort you can definde a regex, and the match group which should be kept
    wordsort_cleanup = defaultdict( lambda: ["(.*)",1],
        {
        "Adjektiv"      : ["^(am )?(.*)$",2],
        "Adverb"        : ["(.*)",1],
        "Verb"          : ["^(.*)(\?|\!)?$",1],
        "Substantiv"    : ["^((?:\(?der\)?|\(?den\)?|\(?die\)?|\(?das\)?|\(?dem\)?|\(?dessen\)?|\(?des\)?|\(?deren\)?)\s*[/,]?\s*)*(.*)$",2]
        # TODO: "Abk\xc3\xrzung"    : ["^(\(?der\)? |\(?den\)? |\(?die\)? |\(?das\)? |\(?dem\)? |\(?dessen\)? |\(?des\)? |\(?deren\)? )?(.*)$",2]
        }
    )

    # values that indicate no entry
    blacklist = set(["—", "–", "?", "-"])

    general_cleanup_post = re.compile("^\s*(.*?)'?\s*$")
    # first do the splitting of words

    for wordsort, wds in list(words.items()):
        for info in wds:

            # create separate entries for each singular/plural form
            split_columns(info, wds, key='Plural')
            split_columns(info, wds, key='Singular')

            # reset variables
            genders = ''
            alternatives = []
            # now the splitting if one entry stands for several words. this is possible in two ways: 1. several wordsorts 2. Nouns with several genders
            if not info['info']:
                info['gender'] = None
                continue
            #already processed
            if info.get('gender'):
                enforce_singular_gender(info)
                continue
            genders = ''.join(re.findall('\{\{[mnf]{0,3}\}\}', info['info'])).replace(' ','').replace('{','').replace('}','')
            genders = ''.join(set(genders)) # remove duplicates
            if wordsort == 'Substantiv' or wordsort == 'Abkürzung':
                alternatives = [info['info']]
            else:
                alternatives = info['info'].split('Wortart')
            if genders == '' and len(alternatives) == 1:
                if wordsort == 'Nachname' or 'Nachname' in info['info']:
                    pass
                elif wordsort == 'Toponym' or 'Toponym' in info['info']:
                    info['gender'] = 'n'
                #TODO: we may be able to extract correct gender for first names from Wiktionary ("Bedeutung: männlicher Vorname")
                elif wordsort == 'Vorname' or 'Vorname' in info['info']:
                    if config.debug_lvl > 0:  print(('no gender specified, (Vorname): ' +  info['lemma']))
                #TODO: those seem to be mostly last names; should we extract this info (from "Bedeutung: Familienname")
                elif wordsort == 'Eigenname' or 'Eigenname' in info['info']:
                    if config.debug_lvl > 0:  print(('no gender specified, (Eigenname): ' +  info['lemma']))
                #TODO: anything we can do here?
                elif wordsort == 'Substantiv' or 'Substantiv' in info['info']:
                    if config.debug_lvl > 0:  print(('no gender specified, (Substantiv): ' +  info['lemma']))
                info['info'] = alternatives[0]
                continue
            elif len(genders) == 1 and len(alternatives) == 1:
                info['info'] = alternatives[0]
                info['gender'] = genders # will be 'm' or 'n' or 'f'
                continue
            # when we come here there is more then one gender or alternative
            # keep the first fino each to the original
            info['info'] = alternatives[0]

            # the rest is for the alternatives
            alternatives = alternatives[1:]
            if config.debug_lvl > 0: print(('SPLITTING of info with Wortart result: ' + str(alternatives) + ' and gender ' + genders + ' (lemma: ' + info['lemma'] + ')'))

            # if there are several genders, make a copy of the original, but with different gender 
            for gender in genders[1:]:
                entry = copy.deepcopy(info)
                entry['gender'] = gender

                words[wordsort].append(entry)

            for i, alt in enumerate(alternatives):
                # look for a new wordsort
                try:
                    alt_wordsort = re.match('\|([^\|]*)\|.*', alt).group(1)
                except:
                    continue

                # fill in with the rest
                # 2. Nouns with several genders
                if len(genders) > 0:
                    for j, gender in enumerate(genders):
                        entry = copy.deepcopy(info)
                        entry['info'] = alt
                        entry['gender'] = gender
                        words[alt_wordsort].append(entry)
                else:
                    entry = copy.deepcopy(info)
                    entry['info'] = alt
                    words[alt_wordsort].append(entry)

            if len(genders) > 0:
                if wordsort == 'Nachname' or 'Nachname' in info['info'] or wordsort == 'Toponym' or 'Toponym' in info['info']:
                    pass
                else:
                    info['gender'] = genders[0]
                    enforce_singular_gender(info)


    for wordsort, wds in list(words.items()):

        for info in wds:

            if not info:
                continue

            verb_particle = None

            for case, caseValues in list(info['cases'].items()):
                if type(caseValues) != list:
                    caseValues = [caseValues]
                new_caseValue = []
                for caseValue in caseValues:
                    ### first remove some html snippets and other always disturbing things
                    caseValue = re.sub("</?small>", "", caseValue)
                    caseValue = re.sub("</?center>", "", caseValue)
                    caseValue = re.sub("’", "", caseValue) # removes ´
                    caseValue = re.sub("<ref>.*", "", caseValue)
                    caseValue = re.sub("<!--.*-->", "", caseValue)

                    # replace '-' with nothing e.g. 'x-beinig' becomes 'xbeinig'
                    caseValue = re.sub('-', '', caseValue)

                    # pre cleanup
                    caseValue = caseValue.strip(' ![]\'\"')

                    # check if entry is deletable
                    if caseValue in blacklist:
                        continue

                    # handle alternative cases sometimes given. Split it into a list.
                    # - e.g. 'krabbl(e)'. 
                    # - sometimes also given like this: 'krabbl / krabble'
                    match = regex_alt_parenthesis.match(caseValue)
                    match2 = regex_alt_brackets.match(caseValue)
                    if match:
                        caseValue_list = []
                        caseValue_list.append(re.sub('\(|\)', '', caseValue))  # just remove parenthesis
                        caseValue_list.append(re.sub('\(.*?\)', '', caseValue)) # remove parenthesis with content
                        caseValue = caseValue_list
                    elif match2:
                        caseValue_list = []
                        caseValue_list.append(re.sub('\[|\]', '', caseValue))  # just remove brackets
                        caseValue_list.append(re.sub('\[.*?\]', '', caseValue)) # remove brackets with content
                        caseValue = caseValue_list
                    else:
                        caseValue = [caseValue]
                    # NOTE: !!! from here on, all casevalues are lists of strings !!! 
                    # NOTE: !!
                    # NOTE: !

                    # split alternatives if there is a '<br />'
                    caseValue = [entry for casev in caseValue for entry in regex_pagebreak.split(casev)]

                    # sometimes a comment (ending with colon) precedes the word form
                    caseValue = [c.split(':',1)[-1] for c in caseValue]

                    # alternatives separated by "," or "/"
                    caseValue = [entry for casev in caseValue for entry in casev.split(", ")]
                    caseValue = [entry for casev in caseValue for entry in casev.split(" / ")]

                    # wordsort specific cleanup
                    if wordsort in wordsort_cleanup:
                        match_group_nr = wordsort_cleanup[wordsort][1]
                        caseValue = [re.match(wordsort_cleanup[wordsort][0], casev).group(match_group_nr) for casev in caseValue]

                    # post cleanup
                    caseValue = [general_cleanup_post.match(casev).group(1) for casev in caseValue]
                    caseValue = [casev.strip(' ![]\'\"') for casev in caseValue]

                    new_caseValue += caseValue

                # filter empty strings and double entries
                caseValues = list(set([x for x in new_caseValue if x != ""]))


                # identify (and discard) separable verb prefix
                if wordsort == 'Verb':
                    for i,caseValue in enumerate(caseValues):
                        casev_splitted = caseValue.split()
                        if len(casev_splitted) > 1:
                            if case == 'Partizip II':
                                caseValues[i] = casev_splitted[-1]
                            else:
                                caseValues[i] = casev_splitted[0]
                                if info['lemma'].startswith(casev_splitted[-1]) and len(casev_splitted[-1]) < len(info['lemma']):
                                    verb_particle = casev_splitted[-1]

                if not caseValues:
                    del(info['cases'][case])
                else:
                    info['cases'][case] = caseValues



            # for adjectives without inflection table, accept it as an uninflected form
            if wordsort == 'Adjektiv' and not info['cases']:
                info['cases'] = {'Positiv': [info['lemma']]}

            # strip separable verb prefix from lemma and Partizip II
            if wordsort == 'Verb' and verb_particle:
                info['lemma'] = info['lemma'][len(verb_particle):]
                if 'Partizip II' in info['cases']:
                    for i,caseValue in enumerate(info['cases']['Partizip II']):
                        info['cases']['Partizip II'][i] = caseValue[len(verb_particle):]

    return words


# if a wiktionary inflection table has multiple plural forms, split it up into separate SMOR entries.
def split_columns(info, info_list, key='Plural'):

    if any(key + ' 2' in case for case in info['cases']):
        i = 2
        exists = True
        split = False
        while exists:
            newinfo = copy.deepcopy(info)
            exists = False
            deleted = False
            for case in list(newinfo['cases']):
                if key in case and key + ' ' + str(i) not in case:
                    deleted = True
                    del newinfo['cases'][case]
                elif key + ' ' + str(i) in case:
                    exists = True
            # if there are at least two columns in the table, split entry
            if exists and deleted:
                split = True
                info_list.append(newinfo)
            i += 1

        if split:
            for case in list(info['cases']):
                if key in case and key + ' 1' not in case and not case.endswith(key):
                    del info['cases'][case]

# when there are multiple singular forms, make sure that we only keep the ones that have the correct gender
def enforce_singular_gender(info):
    gender = info.get('gender')

    allowed = True
    keys = ['Nominativ Singular'] + ['Nominativ Singular ' + str(i) for i in range(1,6)]
    for key in keys:
        if key in info['cases']:
            if gender == 'm' and not 'der ' in info['cases'][key] and not '(der)' in info['cases'][key]:
                allowed = False
                break
            elif gender == 'f' and not 'die ' in info['cases'][key] and not '(die)' in info['cases'][key]:
                allowed = False
                break
            elif gender == 'n' and not 'das ' in info['cases'][key] and not '(das)' in info['cases'][key]:
                allowed = False
                break

    if not allowed:
        info.clear()



# picks a random word
def pickWord(words, wordsort=None):
    if wordsort != None:
        rand_wordsort = wordsort
    else:
        rand_wordsort = sample(list(words.keys()), 1)[0]
    print(("Wordsort:", rand_wordsort))
    return sample(list(words[rand_wordsort].values()), 1)[0]

# this function calls the essential other functions
# @words: is a dictionary created by 'extractFromWikidump'
# NOTE: this function can be seen as an example in which order to call the essential functions
def doAll(words):
    # first clean the words from unnecassary stuff
    print("## do cleanup of cases")
    words = cleanCasesAndSplit(words) #NOTE:from here on, all casevalues are lists of strings (even when only 1 string)
    # extract the smor features
    print("## extract smor features")
    words = extractSmorFeatures(words)
    print("## guess inflectional classes")
    results = generateInflectClasses(words)
    print("## fill hypothesis into words dict")
    # NOTE: a result has the structure [<wordsort>, <wordinfos enriched with possible hypothesis>]
    newwords = defaultdict(list)
    for result in results:
        newwords[result[0]].append(result[1])
    print("## project analyses to abbreviations")
    abbreviation_projection(newwords)
    return newwords


# statistical output of inflectional classes
# TODO: make return value, describe it and do it the same way as morphisto stats
def statsInflectionalClasses(words):
    stats = dict()
    for wordsort, wds in list(words.items()):
        print("### '"+ wordsort +"' inflectional class counts for (total: " + str(len(wds)) + ")")
        counts = defaultdict(int)
        nr_identified = 0 # nr of words only ONE inflectional class was found in the end
        for word, info in list(wds.items()):
            # a list of hypothesis
            try:
                if info['inflectionalClasses'] != None:
                    counts[(" & ").join(sorted(info['inflectionalClasses']))] += 1
                    if len(info['inflectionalClasses']) == 1:
                        nr_identified += 1
                else:
                    counts["(None)"] += 1
            except:
                counts["(None: could not join)"] += 1
        stats[wordsort] = counts
        # print result
        print("IDENTIFIED:", nr_identified, "(thats " + str(nr_identified*1.0/len(wds)) + ")")
        for key in sorted(counts, key=counts.get, reverse=True):
            print("'" + key + "'", " => ", counts[key])
    return stats

# @stats: output from statsInflectionalClasses or statsMorphisto...
def statsPrintPretty(stats, onlyIdentified=True, output_file=None):
    output_string = ''
    for wordsort, counts in list(stats.items()):
        nr_identified = 0 # nr of words only ONE inflectional class was found in the end
        nr_ambi = 0 # ambigious, several infl classes possible
        fail_count = 0
        total = 0
        output_string += "######################## '"+ str(wordsort) + '\n'
        for key in sorted(counts, key=counts.get, reverse=True):
            total += counts[key]
            if not '&' in key and key != '' and key != '(None)':
                nr_identified += counts[key]
                output_string += "===> '" + str(key) + "'" + " => " + str(counts[key]) + '\n'
            else:
                if key == '' or key == '(None)':
                    fail_count += counts[key]
                else:
                    if not onlyIdentified:
                        output_string += "'" + key + "'" + " => " + str(counts[key]) + '\n'
                    nr_ambi += counts[key]
        output_string += "##  total count: " + str(total)  + '\n'
        output_string += "## identified "+ str(nr_identified) + " of wordsort '" + str(wordsort) + "'. That's " + str((100*nr_identified)/(total+0.001)) + " %" + '\n'
        output_string += "## failed "+ str(fail_count) + " of wordsort '" + str(wordsort) + "'. That's " + str(100*fail_count/(total+0.001)) + " %" + '\n'
        output_string += "## ambiguous "+ str(nr_ambi) + " of wordsort '" + str(wordsort) + "'. That's " + str(100*nr_ambi/(total+0.001)) + " %" + '\n'
    print(output_string)
    if output_file != None:
        with open(output_file, "w") as text_file:
            text_file.write(output_string)

# precondition: smor symbols must be generated before, also pos and stem must be extracted
# calls 'generateHypothesis' for each word
# NOTE: this function is the bottleneck of this script and therefore should be parallelized
def generateInflectClasses(words):
    global workers

    # 0. setup queues
    # load up work queue
    work_queue = multiprocessing.Queue()
    # create a queue to pass to workers to store the results
    result_queue = multiprocessing.Queue()

	# 1. first gather jobs for workers
    todo = 0
    for wordsort, wds in list(words.items()):
        for info in wds:
            if not is_complete(info):
                continue
            # be sure it's no default dict (with unpickable functions in it)
            info = mapToDict(info)
            # bundle job. a job consists of the wordsort, the word, and the informations about it
            job = [wordsort, info]
            # add to work queue
            work_queue.put(job)
            todo += 1
    if config.debug_lvl > 0: print(("########## loaded jobs into work queue. There are #" + str(work_queue.qsize()) + " jobs."))

    # 2. create workers and let them work
    workers = []
    for i in range(config.num_processes):
        work_queue.put(None)
        if config.debug_lvl > 0: print("initialize worker")
        workers.append(Worker(work_queue, result_queue))

    for worker in workers:
        if config.debug_lvl > 0: print("start worker")
        worker.start()
    
    # 3. gather results and write them into the words dict
    # collect the results off the queue
    results = []
    finished = 0
    print(("#### Wait till all jobs are done (#" + str(todo - len(results)) + ")"))
    while finished < config.num_processes:
        a_result = result_queue.get()
        if a_result is None:
            finished += 1
        else:
            results.append(a_result)
    print("all jobs are done")
    return results


# filter out entries that are empty or are missing required information, e.g. a part-of-speech
def is_complete(info):
    if not info:
        return False

    # empty part-of-speech, e.g. if heading is "Deklinierte Form"
    if not 'pos' in info or not info['pos']:
        return False

    return True

# this function dumps the fully analysed words like the opensource morphology lexicon morphisto
# e.g.
# <BaseStem>
#   <Lemma>Carabinieri</Lemma>
#   <Stem>Carabinieri</Stem>
#   <Pos>NN</Pos>
#   <Origin>fremd</Origin>
#   <InfClass>NMasc_s_s</InfClass>
# </BaseStem>
# NOTE: only words get dumped which could be assigned to ONE inflectional class, all others will be ignored
def dumpMorphistoLike(words, filename=None):

    #some words are genuinely ambiguous and will be encoded through multiple inflection classes
    allowed_ambiguities = set([
        ("NFem_0_s", "NFem_s_s"), # der Mail(s)
        ("NMasc/Sg_0","NMasc/Sg_s"), # des Islam(s)
        ("NMasc/Sg_0","NMasc/Sg_es"), # des Quatsch(es)
        ("NNeut/Sg_0","NNeut/Sg_s"), # des Utopia(s)
        ("NNeut/Sg_0","NNeut/Sg_es"), # des Gedöns(es)
        ("NMasc-ns","NMasc_n_n"), # des Buchstaben(s)
        ("NMasc_en_en","NMasc_s_en"), # des Typs/Typen
        ("NMasc_0_x", "NMasc_s_s"), # des Pkw(s)
        ("NMasc_0_x", "NMasc_s_x"), # des Western(s)
        ("Name-Masc_0","Name-Masc_s"),
        ("Name-Neut_0","Name-Neut_s"),
        ("Name-Fem_0","Name-Fem_s")
        ])

    # cache to remove duplicates and ensure proper sorting
    cache = set()

    for wordsort, wds in list(words.items()):

        for info in sorted(wds, key=lambda x: x.get('lemma')):
            # a list of hypothesis
            try:
                inflectClasses = info['inflectionalClasses']
            except:
                continue
            if not inflectClasses:
                continue
            if not info["pos"]:
                continue
            if len(inflectClasses) != 1: # there should only be ONE infl class
                if tuple(sorted(inflectClasses)) not in allowed_ambiguities:
                    continue

            if 'origin' in info:
                origin = info['origin']
            else:
                origin = 'nativ'

            # one entry per spelling variant (#TODO: do we want to mark old orthography?)
            lemmas = [info["lemma"]]
            if 'alt_spelling' in info:
                 lemmas += [spelling for spelling in info["alt_spelling"] if not '-' in spelling]

            for lemma in lemmas:
                if info["pos"] == 'V':
                    stem = getVerbStem(lemma)
                elif lemma == info['lemma']:
                    stem = info.get('stem', lemma)
                else:
                    if info.get('stem') == info['lemma']:
                        stem = lemma
                    # need some guessing for cases with a special plural stem *and* alternative spellings (Korpus, Korpora, Corpus)
                    else:
                        stem = guess_stem(info['lemma'], info['stem'], lemma)
                        if not stem:
                            if config.debug_lvl > 0: print(('error in guess_stem ({0} - {1} - {2})'.format(info['lemma'], info['stem'], lemma)))
                            continue

                # skip lowercase nouns (mostly noise, and can allow troublesome compounds)
                if lemma and lemma[0].islower() and (info["pos"] == "NN" or info["pos"] == "NPROP"):
                    continue

                for inflectClass in inflectClasses:
                    # only if it it is a real class go on
                    if inflectClass == None or inflectClass == '' or inflectClass == '(None found)':
                        continue # go to next word

                    if info["pos"] == 'V' and info.get("ge"):
                        ge = True
                    else:
                        ge = False

                    cache.add((info["pos"],lemma,stem,origin,inflectClass,ge))


    if filename == None:
        filename = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + "_morphisto_like" + ".xml"
    if sys.version_info < (3, 0):
        outfile = codecs.open(filename, 'w', encoding='UTF-8')
    else:
        outfile = open(filename,'w', encoding='UTF-8')
    outfile.write('<?xml version="1.0" encoding="utf-8"?>\n')
    outfile.write('<?xml-stylesheet type="text/xsl" href="lexicon-transform.xslt"?>\n')
    outfile.write("<smor>\n")

    for data in sorted(cache):
        writeBaseStem(data, outfile)

    outfile.write("</smor>")
    outfile.close()


def writeBaseStem(data,outfile):
        pos,lemma,stem,origin,inflectClass,ge = data
        lemma = escape(lemma)
        stem = escape(stem)
        outfile.write("\t<BaseStem>\n")
        if ge:
            outfile.write("\t\t<MorphMarker>ge</MorphMarker>\n")
        outfile.write("\t\t<Lemma>"+lemma+"</Lemma>\n")
        outfile.write("\t\t<Stem>"+stem+"</Stem>\n")
        outfile.write("\t\t<Pos>"+pos+"</Pos>\n")
        outfile.write("\t\t<Origin>" + origin + "</Origin>\n")
        outfile.write("\t\t<InfClass>"+inflectClass+"</InfClass>\n")
        outfile.write("\t</BaseStem>\n")


# given a lemma-stem pair (Korpus, Korpora), and an alternative spelling of the lemma (Corpus),
# try to guess the stem in the alternative spelling (Corpora)
def guess_stem(lemma, stem, alt_spelling):

    # get suffix of lemma/stem (by cutting off common prefix)
    i = 0
    for i, (x,y) in enumerate(zip(lemma,stem)):
        if x!=y:
            break
    suffix_lemma = lemma[i:]
    suffix_stem = lemma[i:]

    if alt_spelling.endswith(suffix_lemma):
        alt_spelling_prefix = alt_spelling[:-len(suffix_lemma)]
        return alt_spelling_prefix + suffix_stem
    else:
        return None




# this function returns statistical data evaluated upon the opensource morphisto korpus
# => http://www1.ids-mannheim.de/lexik/home/lexikprojekte/lexiktextgrid/morphisto.html
def statsMorphisto(pathToMorphistoXml):

    print(("Using '" + pathToMorphistoXml + "'"))
    stats = defaultdict(lambda: defaultdict(int))
    # regexes
    r_pos = re.compile(".*<Pos>(.*)<\/Pos>.*")
    r_inflClass = re.compile(".*<InfClass>(.*)<\/InfClass>.*")
    r_word_begin = re.compile(".*<Basestem>.*")
    r_word_end = re.compile(".*<\/Basestem>.*")
    # init vars 
    pos = None
    inflClass = None
    for line in fileinput.input([pathToMorphistoXml]):
        match = r_word_begin.match(line)
        if match != None: # reset vars
            # print("matched begin")
            pos = inflClass = None
        match = r_pos.match(line)
        if match != None:
            # print("matched pos")
            pos = match.group(1)
        match = r_inflClass.match(line)
        if match != None:
            # print("matched infl class")
            inflClass = match.group(1)
        if inflClass != None and pos != None:
            # print("found pair +1")
            stats[pos][inflClass] += 1
            pos = inflClass = None
        match = r_word_end.match(line)
        if match != None: # reset vars
            pos = inflClass = None
    return stats

# worker class for multiprocessing
class Worker(multiprocessing.Process):
    def __init__(self, work_queue, result_queue):
        # base class initialization
        multiprocessing.Process.__init__(self)
        # job management stuff
        self.work_queue = work_queue
        self.result_queue = result_queue
        self.regex_nouns_singular = re.compile("^(.*?)(_.*?)?(_.*)?$") # TODO: move to regex file
        # if a mapping of nouns with only singular cases happens, the following list will be used to check, if the mapped class is legit
        self.singular_mappings = {
          "NNeut-0/ien": "NNeut/Sg_s"
        }
        self.possible_singular_infl_classes = [
         "NFem/Sg",
         "NMasc-s/Sg",
         "NMasc/Sg_0",
         "NMasc/Sg_es",
         "NMasc/Sg_s",
         "NNeut/Sg_0",
         "NNeut/Sg_en",
         "NNeut/Sg_es",
         "NNeut/Sg_s"
        ]
        self.possible_name_classes = [
         "Name-Fem_0",
         "Name-Fem_s",
         "Name-Masc_0",
         "Name-Masc_s",
         "Name-Neut_0",
         "Name-Neut_s",
         "Name-Invar",
         "Name-Pl_0",
         "Name-Pl_x",
        ]

        # just singular/plural forms; mapping of other forms per regex
        self.name_mapping = {
            "N?/Pl_x":     "Name-Pl_x",
            "N?/Pl_0":     "Name-Pl_0",
            "NFem/Sg" :    "Name-Fem_0",
            "NMasc-s/Sg":  "Name-Masc_s",
            "NMasc/Sg_0":  "Name-Masc_0",
            "NMasc/Sg_s":  "Name-Masc_s",
            "NNeut/Sg_0":  "Name-Neut_0",
            "NNeut/Sg_s":  "Name-Neut_s",
        }

        self.static_infl_class = {
            "Adverb"                    : "Adv",
            "Modaladverb"               : "Adv",
            "Partikel"                  : "Adv",
            "Fokuspartikel"             : "Adv",
            "Gradpartikel"              : "Adv",
            "Interrogativadverb"        : "WAdv",
            "Konjunktionaladverb"       : "Adv",
            "Lokaladverb"               : "Adv",
            "Pronominaladverb"          : "ProAdv",
            "Temporaladverb"            : "Adv",
            "Konjunktion"               : "Konj-Kon",
            "Subjunktion"               : "Konj-Sub",
            "Vergleichspartikel"        : "Konj-Vgl",
            "Interjektion"              : "Intj",
            "Grußwort"                  : "Intj",
            "Grußformel"                : "Intj",
            "Onomatopoetikum"           : "Intj",
            "Antwortpartikel"           : "Ptkl-Ant",
            "Negationspartikel"         : "Ptkl-Neg"
            # TODO: Numerale ?
        }

        # if 'NMasc/Sg_s' accepts a subset of 'NMasc/Sg_es'. If both are valid analyses, and there is an -es Genitive in Wiktionary, remove the _s-analysis
        self.s_es_mapping = {
            'NMasc/Sg_s':   'NMasc/Sg_es',
            'NMasc_s_e':    'NMasc_es_e',
            'NMasc_s_en':   'NMasc_es_en',
            'NNeut/Sg_s':   'NNeut/Sg_es',
            'NNeut_s_e':    'NNeut_es_e',
            'NNeut_s_en':   'NNeut_es_en'
        }

        self.family_name_map = {
            'NMasc_s_s':    'FamName_s',
            'NNeut_s_s':    'FamName_s',
            'NMasc/Sg_s':   'FamName_s', #SMOR currently doesn't support singular-only family names
            'NNeut/Sg_s':   'FamName_s',
            'NFem/Sg':      'FamName_0',
            'NFem_0_s':     'FamName_s',
            'NFem_s_s':     'FamName_s',
            'NMasc_0_x':    'FamName_0',
            'NFem_0_x':     'FamName_0',
            'NNeut_0_x':    'FamName_0',
            'NMasc/Sg_0':   'FamName_0',
            'NNeut/Sg_0':   'FamName_0',
            }

        self.plural_mapping = {
            'm': ['NMasc/Pl'],
            'f': ['NFem/Pl'],
            'n': ['NNeut/Pl']
            }

    def run(self):
        self.fst_analyser = FstWrapper()
        while True:

            # get a task
            if config.debug_lvl >  0: print(("a worker wants to get a job (one of #" + str(self.work_queue.qsize()) + " left)"))
            job = self.work_queue.get()
            if job is None:
                self.result_queue.put(None)
                break
            if config.debug_lvl > 1: print(("worker gotta job => " + str(job)))
            word_sort = job[0]
            word_infos = job[1]
 
            # the actual processing
            # check if static infl class mapping is there
            if word_sort in self.static_infl_class:
                mapped_static_infl_class = self.static_infl_class[word_sort] 
                # insert the found static infl class into the word_information
                word_infos['inflectionalClasses'] = [mapped_static_infl_class]
                job[1] = word_infos
                # store the result
                if config.debug_lvl > 0: print(("a worker got a job (#" + str(self.work_queue.qsize()) + " jobs left) (pos is:" + str(word_infos['pos']) +") => static map to: " + mapped_static_infl_class))
                self.result_queue.put(job)
                continue # go back to top of while loop

            elif word_sort == 'Abkürzung':
                abbreviation_heuristics(word_infos)
                self.result_queue.put(job)
                continue

            if config.debug_lvl > 0: print(("a worker got a job (#" + str(self.work_queue.qsize()) + " jobs left) (pos is:" + str(word_infos['pos']) +")"))

            hypothesis = self.generateHypothesis(word_infos) ######################## HERE the hypothesis gets generated
            original_hypothesis = copy.deepcopy(hypothesis) # we can fallback to this, if we filter too much

            #### post processing of hypothesis
            # special case for Nouns: if there are only singuar (or only plural) cases, then map the inflectional classes
            if word_infos['pos'] == "NN":
                only_singular = True
                only_plural = True
                for casename, casesmorfeatures in list(word_infos['smor_features'].items()):
                    if not ('<Sg>' in casesmorfeatures):
                        only_singular = False
                    elif not ('<Pl>' in casesmorfeatures):
                        only_plural = False
                if only_singular:
                    hypothesis = self.singular_mapping(hypothesis)

                elif only_plural:
                    if all(hypo.endswith('_x') for hypo in hypothesis):
                        hypothesis = ['N?/Pl_x']
                    elif all(hypo.endswith('_0') for hypo in hypothesis):
                        hypothesis = ['N?/Pl_0']

                # if no inflection class is found, try to find a pair of classes (one singular class, one plural class) that predicts all word forms
                elif not hypothesis:
                    singular_hypothesis = self.singular_mapping(set.intersection(*[word_infos['analysed_as'][case][-1] for case in word_infos['analysed_as'] if 'Singular' in case]))
                    singular_hypothesis = self.disambiguate_es_s(word_infos, singular_hypothesis)
                    plural_hypothesis = self.plural_mapping.get(word_infos.get('gender'), [])
                    if len(singular_hypothesis) == 1 and len(plural_hypothesis) == 1:
                        hypothesis = singular_hypothesis
                        plural_forms = [word_infos['cases'][case][0] for case in word_infos['cases'] if 'Plural' in case]
                        # if all plural forms are the same, we can generate an entry for it
                        if len(set(plural_forms)) == 1 and not ' ' in plural_forms[0]:
                            pluralentry = copy.deepcopy(word_infos)
                            pluralentry['stem'] = plural_forms[0]
                            if config.debug_lvl > 0: print(("separate plural stem: {0} - {1}".format(word_infos['lemma'], pluralentry['stem'])))
                            pluralentry['inflectionalClasses'] = plural_hypothesis
                            del pluralentry["analysed_as"]
                            del pluralentry["smor_features"]
                            self.result_queue.put((job[0], pluralentry))


                # umlaut filter: sles may allow inflection class with umlautung, even if there is no vowel that can have umlaut
                lemma_umlaut_count = len(re.findall('ö|ä|ü|Ü|Ä|Ö', word_infos['lemma']))
                umlautung = False
                for v in list(word_infos['cases'].values()):
                    for vv in v:
                        if lemma_umlaut_count < len(re.findall('ö|ä|ü|Ü|Ä|Ö', vv)):
                            umlautung = True
                            break
                    if umlautung: break
                if hypothesis and not umlautung:
                    # only keep hypothesis which do not contain '$'. (no umlaut in plural)
                    hypothesis = [x for x in hypothesis if not '$' in x]

                hypothesis = self.disambiguate_es_s(word_infos, hypothesis)

                # mapping of names
                if (word_infos['info'] and len(re.findall('Nachname', word_infos['info'])) > 0) or word_sort == 'Nachname':
                    word_infos['pos'] = 'NPROP'
                    hypothesis = sorted(set([self.family_name_map.get(hypo,hypo) for hypo in hypothesis]))

                elif word_infos['info'] and 0 < len(re.findall('Eigenname|Vorname|Toponym', word_infos['info'])) or word_sort in ['Eigenname','Vorname','Toponym']:
                    word_infos['pos'] = 'NPROP'
                    for i, hypo in enumerate(hypothesis):
                        if hypo in self.name_mapping:
                            hypothesis[i] = self.name_mapping[hypo]
                        else:
                            match = self.regex_nouns_singular.search(hypo)
                            gender = match.group(1)[1:]
                            newhypo = 'Name-' + gender + (match.group(2) or "")
                            if newhypo in self.possible_name_classes:
                                hypothesis[i] = newhypo
                            else:
                                if config.debug_lvl > 0: print(newhypo  + " is  not in " + str(self.possible_name_classes))

                    #duplicate removal
                    hypothesis = sorted(set(hypothesis))

            elif word_infos['pos'] == 'V':
                # NOTE: special case for Verbs. if there are only the analysis VVReg-el/er and VVReg, they can be desambiguiated by the ending
                if len(hypothesis or []) == 2 and ("VVReg-el/er" in (hypothesis or [])) and ("VVReg" in (hypothesis or [])):
                    word = word_infos['lemma']
                    word_end = word[len(word_infos['stem']):]
                    if word_end == 'en':
                        if config.debug_lvl > 0: print("Special case verb: desambiguate VVReg vs. VVReg-el/er => VVReg wins")
                        hypothesis = ['VVReg']
                    else:
                        if config.debug_lvl > 0: print("Special case verb: desambiguate VVReg vs. VVReg-el/er => VVReg-el/er wins")
                        hypothesis = ['VVReg-el/er'] 

            elif word_infos['pos'] == 'ADJ':
                hypothesis = adjective_filter(word_infos, hypothesis)

            # insert the generated hypothesis into the word_information
            if hypothesis:
                word_infos['inflectionalClasses'] = hypothesis
            else: # fallback to original generated hypothesis when there is no hypothesis left after all the filtering TODO: eventuelly not the best way 
                word_infos['inflectionalClasses'] = original_hypothesis

            job[1] = word_infos
            # store the result
            self.result_queue.put(job)

    # NOTE: the name of this function is kind of misleading cause the ANALYSE method of the fst_wrapper is used
    # precondition: smor symbols must be generated before
    def generateHypothesis(self, word):

        caseInflectClasses = [] # a list of sets
        word['analysed_as'] = defaultdict(list)
        for caseName, caseValue in list(word['cases'].items()):
            caseInflectClass = set()
            for casev in caseValue:
                casev = reformatForAnaly(word, casev)
                if casev == '':
                    continue
                word['analysed_as'][caseName].append(casev)
            caseHypothesis = []
            for casev in word['analysed_as'][caseName]:
                tmp_analysis = self.fst_analyser.analyse(casev)
                caseHypothesis += tmp_analysis

            stem = word['stem']
            stem_reformat = reformatForAnaly(word, stem)
            caseHypothesis = self.fst_analyser.filterAnalysis(caseHypothesis, word['smor_features'][caseName], stem_reformat, word['pos'])

            # TODO: generation doesn't currently seem to have a purpose, since the possible use cases (inflection class correctly analyzes all forms, but overgenrates)
            # are currently handled by special heuristics (e.g. singular-only nouns or optional e-elision in genitive). delete this if no other need for generation comes up.

            ## after the raw filteringm we go in the other direction and let the fst generate the possible forms. all if this forms must be entries in wiktionary
            #new_caseHypothesis = []
            #for caseh in caseHypothesis:
                #gen_forms = self.fst_analyser.generate(caseh)
                #if gen_forms == None:
                    #continue # go to next case
                ## at least one generated form must be found as entries
                #good_hypothesis = False
                #for gen_form in gen_forms:
                    #if gen_form in word['analysed_as'][caseName]:
                        #good_hypothesis = True
                #if good_hypothesis: # if the hypothesis still is good, add it to the new_caseHypothesis
                    #new_caseHypothesis.append(caseh)
            #caseHypothesis = new_caseHypothesis

            # at last we can determine the possible inflectional classes for this case
            for caseHypo in caseHypothesis:
                inflClass = self.fst_analyser.determineInflClass(caseHypo)
                if inflClass != None:
                    caseInflectClass.add(inflClass)
            word['analysed_as'][caseName].append(caseInflectClass)
            caseInflectClasses.append(caseInflectClass)

            if '<PPast>' in word['smor_features'][caseName] and any(casev.startswith('<ge>') for casev in caseHypothesis):
                word['ge'] = True

        # finally produce the intersection of all the sets
        if config.debug_lvl > 1: print((">>>>>>>>>>>>>>>> before insection:" + str(caseInflectClasses)))
        word['analysed_as']['XbeforeIntersectionX'] = copy.deepcopy(caseInflectClasses)
        if len(caseInflectClasses) > 1:
            intersection = list(set.intersection(*caseInflectClasses))
            word['analysed_as']['XafterIntersectionX'] = copy.deepcopy(intersection)
            if config.debug_lvl > 1: print("<<<<<<<<<<<<<< Intersection: ", intersection)
            if intersection == []: 
                if config.debug_lvl > 0: print(("could not find a intersection of these inflectional classes", str(caseInflectClasses))) 
            return intersection 
        elif len(caseInflectClasses) == 1:
            return list(*caseInflectClasses)
        else:
            return []

    def singular_mapping(self, hypothesis):
        mapped_hypothesis = []

        for hypo in (hypothesis or []) :
            if hypo in self.singular_mappings:
                singular_infl_class = self.singular_mappings[hypo]
            else:
                match = self.regex_nouns_singular.match(hypo)
                singular_infl_class = match.group(1) + "/Sg" + (match.group(2) or "")
                singular_infl_class_fallback = match.group(1) + "/Sg"
            # filter arising inflClasses not all are possible
            if singular_infl_class in self.possible_singular_infl_classes:
                mapped_hypothesis.append(singular_infl_class)
            elif singular_infl_class_fallback in self.possible_singular_infl_classes:
                mapped_hypothesis.append(singular_infl_class_fallback)
            else:
                if config.debug_lvl > 0: print(singular_infl_class + ' and ' + singular_infl_class_fallback + " are not in " + str(self.possible_singular_infl_classes))
        mapped_hypothesis = list(set(mapped_hypothesis))
        if config.debug_lvl > 0: print(("mapped classes are: ", mapped_hypothesis))
        return mapped_hypothesis

    # special case _es and _s Genitiv. only take _es if there is at least one casevalue which has the ending 'es'
    def disambiguate_es_s(self, info, hypothesis):
        if any(hypo in self.s_es_mapping and self.s_es_mapping[hypo] in hypothesis for hypo in hypothesis):
            es_genitive = has_es_genitive(info)
            for hypo in list(hypothesis):
                if hypo in self.s_es_mapping and self.s_es_mapping[hypo] in hypothesis:
                    if es_genitive:
                        hypothesis.remove(hypo)
                    else:
                        hypothesis.remove(self.s_es_mapping[hypo])
        return hypothesis

#singular-only adjectives and dealing with optional e in superlative
def adjective_filter(word, hypotheses):

    if len(word['cases']) == 1 and 'Positiv' in word['cases']:
        return ['AdjPos']

    # Adj+(e) marks optional 'e' before 'sten'
    if "Adj+e" in hypotheses and "Adj+" in hypotheses:
        return ["Adj+(e)"]

    # sometimes 'Adj$e' is predicted for stems that cannot have umlaut.
    elif "Adj+e" in hypotheses and "Adj$e" in hypotheses:
        return ["Adj+e"]
    elif "Adj+" in hypotheses and "Adj$" in hypotheses:
        return ["Adj+"]

    # Adj+ allows 'düsterer'; Adj-el/er allows 'düstrer' and 'düsterer'.
    # if 'düstrer' is not in Wiktionary, sles predicts both and we choose "Adj+"
    elif "Adj+" in hypotheses and "Adj-el/er" in hypotheses:
        return ["Adj+"]

    return hypotheses

# check if at least one genitive word form ends in -es
# used for disambiguation between -es and -s inflection classes
def has_es_genitive(word_infos):
    for casename in list(word_infos['cases'].keys()):
        if 'Genitiv' in casename:
            for casev in word_infos['cases'][casename]:
                if casev[-2:] == 'es':
                    return True
    return False


abbr_map = {
            'NN': {
                   'm': 'Abk_NMasc',
                   'f': 'Abk_NFem',
                   'n': 'Abk_NNeut',
                   'ohne feststehendes Genus': 'Abk_NN'},
            'NE': {
                   'm': 'Abk_NEMasc',
                   'f': 'Abk_NEFem',
                   'n': 'Abk_NENeut',
                   'ohne feststehendes Genus': 'Abk_NE'}
            }


# if abbreviation links to Wiktionary page with full meaning, project POS and gender information to abbreviation entry
def abbreviation_projection(words):

    # get link to full page for each entry, and map it to entry itself
    abbr_projection_map = {}
    abbreviations = words['Abkürzung']
    for entry in abbreviations:
        if not entry.get('inflectionalClasses') and 'meaning' in entry:
            abbr_projection_map[entry['meaning']] = entry

    for category in words:
        for entry in words[category]:
            if entry['lemma'] in abbr_projection_map:
                abbr_entry = abbr_projection_map[entry['lemma']]
                # take info from full word entry, and use it to predict class of abbreviation entry
                if not abbr_entry.get('inflectionalClasses'):
                    abbreviation_heuristics(abbr_entry, entry.get('pos'), entry.get('gender'), entry.get('inflectionalClasses'))
                # don't redo heuristics if there are multiple entries for the same word
                if abbr_entry.get('inflectionalClasses'):
                    del abbr_projection_map[entry['lemma']]


# for abbreviations, we sometimes don't know the correct POS / gender etc.
def abbreviation_heuristics(word, pos=None, gender=None, infl_class=None):

    inflection = None
    if not gender:
        gender = word.get('gender')

    if not gender:
        try:
            nom_sg = [word['cases'][case] for case in word['cases'] if 'Nominativ Singular' in case][0][0]
            if 'der ' in nom_sg or '(der)' in nom_sg:
                gender = 'm'
            elif 'die ' in nom_sg or '(die)' in nom_sg:
                gender = 'f'
            elif 'das ' in nom_sg or '(das)' in nom_sg:
                gender = 'n'
        except IndexError:
            pass

    if word['info'] and (pos == 'NE' or 'Eigenname' in word['info'] or 'Vorname' in word['info'] or 'Toponym' in word['info']):
        inflection = abbr_map['NE'].get(gender)

    elif word['info'] and (pos == 'NN' or 'Substantiv' in word['info']):
        inflection = abbr_map['NN'].get(gender)

    # no information about part-of-speech, but we know that word has a gender: assume normal noun
    elif gender:
        inflection = abbr_map['NN'].get(gender)

    # no inflection found, but we know POS
    if not inflection:
        if pos == 'NE' or (word['info'] and (pos == 'NE' or 'Eigenname' in word['info'] or 'Vorname' in word['info'] or 'Toponym' in word['info'])):
            inflection = abbr_map['NE']['ohne feststehendes Genus']

        elif pos == 'NN' or (word['info'] and (pos == 'NN' or 'Substantiv' in word['info'])):
            inflection = abbr_map['NN']['ohne feststehendes Genus']

        elif pos == 'ADJ':
            inflection = 'Abk_ADJ'
        elif pos == 'ADV':
            inflection = 'Abk_ADV'
        elif pos == 'OTHER' and infl_class and infl_class[0] == 'Konj-Kon':
            inflection = 'Abk_KONJ'

    if inflection:
        word['inflectionalClasses'] = [inflection]
    else:
        word['inflectionalClasses'] = []


def reformatForAnaly(word, casev):

    # NOTE: POS Independent word modification just for analysis
    # NOTE: just for the analysis numbers, '-' and ' ' get  removed
    casev = re.sub("\d","", casev)
    casev = re.sub("-","", casev)
    casev = re.sub(" ","", casev)
    casev = re.sub(",","", casev)
    casev = re.sub("\xad","", casev)
    casev = re.sub("–","", casev)

    if word['pos'] == 'NN':
        casev = casev.lower()
        casev = casev.capitalize()
    else:
        casev = casev.lower()

    return casev

# NOTE: a dict with analysed words is expected as argument (e.g. output of 'doAll' function)
def extractFailedAnalysis(words):
    failed_words = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict())))
    for wordsort, wds in list(words.items()):
        for word, info in list(wds.items()):
            try:
                iC = info['inflectionalClasses']
                if iC == '(None found)' or iC == None or iC == "None" or iC == "" or iC == [] or iC == '(None)':
                    failed_words[wordsort][word] = info
            except KeyError:
                failed_words[wordsort][word] = info
    return failed_words


if __name__ == '__main__':

    if len(sys.argv) != 2:
        sys.stderr.write('Usage: {0} dewiktionary-XXX-pages-articles-multistream.xml output_file\n'.format(sys.argv[0]))

    words = extractFromWikidump(sys.argv[1])
    #dumpJSON(words, filename='wiktionary-raw-debug.json')
    newwords = doAll(words)
    #dumpJSON(newwords, filename='wiktionary-debug.json')
    dumpMorphistoLike(newwords, filename=sys.argv[2])
