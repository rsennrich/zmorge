#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import re
import fileinput 
import time
from collections import defaultdict
from datetime import datetime
from random import sample
import yaml
import wiktionary_config as config
import multiprocessing 
import sys
import string
import copy

try:
    from yaml import CLoader as Loader, CDumper as Dumper, CSafeDumper as SafeDumper
except ImportError:
    print "could not load the faster cloader/cdumper/csafedumper for yaml package.\n will load standard loader/dumper"
    from yaml import Loader, Dumper, SafeDumper

from fst_wrapper import FstWrapper # interactive interface for ... TODO: better description
import wik_regex    # collection of regexes used
import wiktionary_config as config # configs in here

########## TODO / TODOs
# - wordsort => manchmal mehrere möglich! regex anpassen wie auch code!
# - mehre Arten von deklinieren möglich, statt nur ein Wert mit Liste lösen
# - Logger einfügen (elegant durch print ersetzung!)
#   à la:
#    import logging
#    logging.basicConfig(filename='example.log',level=logging.DEBUG)
#    logging.debug('This message should go to the log file')
#    logging.info('So should this')
#    logging.warning('And this, too')

# NOTE: debug_lvl can be adjusted in wiktionary_debug_lvl.py

print("Debug is " + ( "ON (level: " + str(config.debug_lvl) + ")"  if config.debug_lvl > 0 else "OFF" ))

workers = [] # NOTE: one global variable ... isnt that ugly ?

# NOTE: this function is from a forum http://mail.python.org/pipermail/tutor/2009-October/072483.html
def mapToDict(d):
    """recursively convert defaultdicts into regular dicts"""
    d = dict(d)
    d.update((k, mapToDict(v)) for k,v in d.items() if isinstance(v, defaultdict))
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


# this function will be called to generate the final output after the inflectional classes where guessed 
#   for each word.
# TODO: ... an example ...
def writeFinalOutputXml(words):
    pass # TODO: ...

def extractFromWikidump(wikidump_filepath=None):
    if wikidump_filepath == None:
        if config.debug_lvl > 0: # if debug, load smaller text file 
            wikidump_filepath = config.debug_wikidump
        else: # do it with real (huge!) file
            wikidump_filepath = config.nondebug_wikidump
    print("reading file '" + wikidump_filepath + "'")
    ######## preparing data structure
    ## structure: wordsort > word > cases > case > value
    ##                            > wordsort additional informational
    words = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict())))


    ######## preparing regexes
    extract_state = False
    # extract state de- & activator regexes
    extract_state_activator =   re.compile(wik_regex.activator)
    extract_state_deactivator = re.compile(wik_regex.deactivator)
    # extractor regex
    extractor_word =        re.compile(wik_regex.word)
    extractor_wordsort =    re.compile(wik_regex.wordsort)
    # extractor_verbtable =        re.compile(wik_regex.verbtable)
    extractor_cases =       re.compile(wik_regex.cases)

    # filters after base-extraction
    filter_non_linguistic_case = re.compile("^(Bild|Weitere_|Hilfsverb|keine weiteren)") # TODO: move to wik_regex

    # variables for context information
    last_word = None
    last_wordsort = None
    last_wordsort_additional_info = None
    # reads file line by line without keeping the already read lines in memory
    line_nr = 0
    count_alternatives = 0
    for line in fileinput.input([wikidump_filepath]):
        line_nr += 1
        if extract_state == False:
            try:
                last_word = extractor_word.match(line).group(1)
                if last_word != None:
                    # kill other informations from before
                    last_wordsort = None
                    last_wordsort_additional_info = None

            except:
                pass
            try:
                # only look for wordsort if word was detected
                if last_word != None:
                    last_wordsort = extractor_wordsort.match(line).group(2)
                    last_wordsort_additional_info = extractor_wordsort.match(line).group(3)
            except:
                pass
            matches = extract_state_activator.match(line)
            if matches and last_word and last_wordsort:
                if config.debug_lvl > 0: print "############ Try to extract for:", last_word, last_wordsort, matches.groups()
                extract_state = True
                # check if there is already an entry, when yes create an alternative name
                if words[last_wordsort].get(last_word) != None:
                    last_word = last_word + ' XALTERNATIVEX ' + str(line_nr)
                    count_alternatives += 1
                    print('Created alternative entry!!!!!! (it is the #' + str(count_alternatives) + 'alt) : ' + last_word)
        elif extract_state == True:
            # first check if we are still in the zone of interest
            matches = extract_state_deactivator.match(line)
            if matches != None:
            # stop extract mode if no match for '^\|.*=.*' can be found
            #matches = extractor_cases.match(line)
            # if matches == None:
                if config.debug_lvl > 0: print("############### stop extraction gracefully here")
                extract_state = False
                # reset found context
                # last_word = None
                last_wordsort = None
                last_wordsort_additional_info = None
                # go to next line
                continue
            # now let's extract
            try:
                case, word_in_case = extractor_cases.match(line).groups()
                if config.debug_lvl > 0: print "## extraction: ", last_word, ":", case, "=>", word_in_case
                # add it into data structure
                # TODO do filtering more elegant and quickly adjustable 
                if word_in_case == "\xe2\x80\x94":
                    if config.debug_lvl > 0: print "Found 'Spiegelstrich'. dont add it " 
                    continue # go to next line, its just a longer '-'
                if filter_non_linguistic_case.match(case) != None:
                    if config.debug_lvl > 0: print "Found non-linguistic case. dont add it " 
                    continue # go to next line
                words[last_wordsort][last_word]["cases"][case] = word_in_case
                words[last_wordsort][last_word]["info"] = last_wordsort_additional_info
            except:
                if config.debug_lvl > 0: print("EXCEPTION. jump to next line") # TODO: better handling ?
                if config.debug_lvl > 0: print("=> could not parse line: " + line)
                #extract_state = False
                # reset found context
                #last_word = None
                #last_wordsort = None
                #last_wordsort_additional_info = None
                # go to next line
                continue
    return words

# NOTE: automatically transforms defaultdicts to dicts 
def dumpYaml(words, filename=None):
    #if config.debug_lvl == 0:
    print  "dump into yaml file (this could take a while)"
    if filename == None:
        filename = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + "_wikiwords" + ".yaml"
    stream = file(filename,'w')
    yaml.dump(mapToDict(words), stream, Dumper=Dumper, allow_unicode=True)
    # yaml.safe_dump(mapToDict(words), stream=stream, allow_unicode=True) # TODO: makes yaml unloadable

# any yaml can be loaded with this function
def loadYaml(filePath):
    stream = file(filePath, 'r')
    return yaml.load(stream, Loader=Loader)

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
        # TODO: "?????" : "<NoGend>"
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
        "Gegenwart" : "<Pres>", # TODO
#        "Vergangenheit": "...", # TODO
#        "Befehl": "...", # TODO
#        "_ich": "<1>", # TODO # TODO: evt optionales smor feature
#        "_du": "<2>", # TODO # TODO: evt optionales smor feature
#        "_er": "<3>", # TODO # TODO: evt optionales smor feature
#        "_ihr": "<2>", # TODO# TODO: evt optionales smor feature
        "schwach": "<Wk>", 
        "stark": "<St>", 
#        "gemischt": "...", # TODO
        "Indikativ": "<Ind>", # TODO
        "Konjunktiv": "<Konj>", # TODO
#        "Partizip": "...", # TODO
#        "Hilfsverb": "...", # TODO
        # "Imperfekt" : "<Imp>", # TODO: check this (left side)
        #"irgendwas_hier" : "<Subj>", # TODO: check this (left side)
        # TODO: important features todo: <Past>
    }
    wordsort_pos = {
        "Adjektiv"                  : "ADJ",
        "Adverb"                    : "ADV",
        "Artikel"                   : "ART",
        "Verb"                      : "V",
        "Hilfsverb"                 : "V",
        "Präposition"               : "PREP",
        "Konjunktion"               : "CONJ",
        "Substantiv"                : "NN", 
        "Vorname"                   : "NN", # NOTE: wrong but for analysation ok #TODO: readjust pos tag add the end
        "Nachname"                  : "NN",# NOTE: wrong but for analysation ok #TODO: readjust pos tag add the end 
        "Eigenname"                  : "NN",# NOTE: wrong but for analysation ok #TODO: readjust pos tag add the end 
        "Toponym"                   : "NN",# NOTE: wrong but for analysation ok #TODO: readjust pos tag add the end ? 
        "Fokuspartikel"         	: "ADV",
        "Gradpartikel"          	: "ADV",
        "Interrogativadverb"    	: "ADV", # TODO: is this ok, is there a special pos for "WAdv",
        "Konjunktionaladverb"   	: "ADV",
        "Lokaladverb"           	: "ADV",
        "Pronominaladverb"      	: "PAV",
        "Temporaladverb"        	: "ADV",
        "Subjunktion"               : "CONJ", # TODO: is this ok, is there a special pos for "Konj-Sub",
        "Vergleichspartikel"        : "CONJ", # TODO: is this ok, is there a special pos for "Konj-Vgl",
        "Interjektion"              : "ITJ",
        "Grußwort"              	: "ITJ",
        "Grußformel"            	: "ITJ",
        "Onomatopoetikum"       	: "ITJ",
        "Antwortpartikel"           : "PTKANT",
        "Negationspartikel"         : "PTKNEG"
    }

    # compile regexes
    for feature_lvl in [wordsort_features, gender_features, wordcase_features]:
        for key, value in feature_lvl.items():
            feature_lvl[re.compile(".*" + key + ".*")] = value # TODO: dangerous compile? 
            del(feature_lvl[key]) # delete old entry

    
    # now let's do the big work
    for wordsort, wds in words.items():
        # at this level extract wordsort sepcific features e.g. pos-class, TODO: more? 
        # this info will added below to each of the words of this wordsort
        wordsort_smor_features = []
        pos = None
        # get the POS (part of speech) information for free
        if wordsort in wordsort_pos.keys():
            pos = wordsort_pos[wordsort] 
        for feature_regex, feature in wordsort_features.items():
            if feature_regex.match(wordsort) != None or feature_regex.match((pos or '')) != None:            
                if config.debug_lvl > 0: print "Matched wordsort => add feature: " + feature
                wordsort_smor_features.append(feature)

        for word, info in wds.items():
            # at this level extract word specific features e.g. gender for nouns
            word_smor_features = []
            for feature_regex, feature in gender_features.items():
                try:
                    if feature_regex.match(info['gender']) != None:
                        word_smor_features.append(feature)
                except:
                    pass

            # prepare smor features dict
            info["smor_features"] = defaultdict(list)
            for case, case_value in info['cases'].items():
                # at this level extract wordcase specific features e.g. case (nominatic, accustativ), time ...
                wordcase_smor_features = []
                for feature_regex, feature in wordcase_features.items():
                    if feature_regex.match(case) != None:            
                        wordcase_smor_features.append(feature)

                # finally combine the features from all levels 
                info["smor_features"][case] = wordsort_smor_features + word_smor_features + wordcase_smor_features
            # save pos
            info["pos"] = pos
            ### extract the stem
            # special case Verbs
            word_stripped = stripAlternative(word)
            if pos == "V":
                stem = lemma = getVerbLemma(word_stripped) #TODO: the word key is still a tuple
            else:
                stem = lemma = word_stripped # TODO: the word key is still a tuple
            info["stem"] = stem
            info["lemma"] = lemma
    return words

def stripAlternative(word):
    # check if string
    if type(word) != str: return None
    # search alternative marker index
    alt_index = word.find(' XALTERNATIVEX')
    if alt_index == -1: # not found
        return word
    else:
        return word[:alt_index]

def getVerbLemma(verb): # TODO: CHECKBF
    if verb[-2:] == 'en':
        return verb[:-2]
    elif verb[-3:] == 'ern' or verb[-3:] == 'eln':
        return verb[:-1] 
    else:
        if config.debug_lvl > 0: print("!!!! COULD NOT determine verbstem of '" + verb + "'")
        return None # TODO: ok ?
# just an info function
# prints wordsorts and number of words for each
def wordStats(words):
    print "#### wordsort and count each"
    for k,v in words.items():
        print k, "=>" , len(v)

# just an info function
def extractPossibleCases(words):
    all_cases = set()
    for wordsort, wds in words.items():
        for word, info in wds.items():
            for case in info['cases'].keys():
                all_cases.add(case)
    return all_cases

# cleans casevalues AND finds possible alternatives
# NOTE: after this function every casevalue is a list of strings (even if there is only one string)
def cleanCasesAndSplit(words):
    # ######### here we define cleanup regexes (in the values) for wordsorts
    # TODO s for wordsort cleanup
    # - bei verben: affix versetzung e.g. 'federt ab' => SCHWIERIG ...
    # - generel: alternativen detekten und zulassen e.g. 'dem Bügelbrett&lt;br /&gt;dem Bügelbrette'
    # - generel: cases mit namen 'Bild' / "Weitere..." killen
    # DONE
    # - generel: alle töten die nur '—' haben (spezieller spiegelstrich) => bedeutet es, dass keine info vorhanden ist oder gleich wie Grundform? konstant? => wenn nicht kill it with fire!
    # - bei verben: '!', 'zu'
    # - bei Substantiven: Artikel
    # - bei adjektiven/adverben: im superlativ 'am' wegschneiden
    # - generel: whitespaces weg machen (am anfang/ende) als erster & letzter schritt
    # NOTE: only words will be processed that match one of these wordsorts
    extract_wordsort = re.compile("(.*)") # ALL
    # extract_wordsort = re.compile(".*(Adjektiv|Adverb|Verb|Substantiv).*")
    # extract_wordsort = re.compile(".*(Substantiv).*") # only nouns
    general_cleanup_pre = re.compile("^\s*(.*?)\s?!?\s*$") # TODO check this regex
    # TODO: remove ' and ´
    regex_alt_parenthesis = re.compile(wik_regex.alt_parenthesis)
    # for each wordsort you can definde a regex, and the match group which should be kept
    wordsort_cleanup = defaultdict( lambda: ["(.*)",1],
        {
        "Adjektiv"      : ["^(am )?(.*)$",2],
        "Adverb"        : ["(.*)",1],
        "Verb"          : ["^(.*)(\?|\!)?$",1],
        "Substantiv"    : ["^(\(?der\)? |\(?den\)? |\(?die\)? |\(?das\)? |\(?dem\)? |\(?dessen\)? |\(?des\)? |\(?deren\)? )?(.*)$",2]
        # TODO: "Abk\xc3\xrzung"    : ["^(\(?der\)? |\(?den\)? |\(?die\)? |\(?das\)? |\(?dem\)? |\(?dessen\)? |\(?des\)? |\(?deren\)? )?(.*)$",2]
        }
    )
    general_cleanup_post = re.compile("^\s*(.*?)'?\s*$")
    # first do the splitting of words

    for wordsort, wds in words.items():
        for word, info in wds.items():
            # reset variables
            genders = ''
            alternatives = []
            # now the splitting if one entry stands for several words. this is possible in two ways: 1. several wordsorts 2. Nouns with several genders
            if not info['info']:
                info['gender'] = None
                continue
            info['gender'] = None
            genders = string.join(re.findall('\{\{[mnf]{0,3}\}\}', info['info'])).replace(' ','').replace('{','').replace('}','') # TODO: eventually risky, check results
            genders = ''.join(set(genders)) # remove duplicates 
            alternatives = info['info'].split('Wortart')
            if genders == '' and len(alternatives) == 1:
                info['info'] = alternatives[0]
                continue
            elif len(genders) == 1 and len(alternatives) == 1:
                info['info'] = alternatives[0]
                info['gender'] = genders # will be 'm' or 'n' or 'f'
                continue
            # when we come here there is more then one gender or alternative
            # keep the first fino each to the original
            info['info'] = alternatives[0]
            orig_cases = copy.deepcopy(info['cases'])
            if len(genders) > 0:
                info['gender'] = genders[0]
                # overwrite cases
                info['cases'] = {}
                for key, value in orig_cases.items():
                    # keep the general ones (without the number at the end)
                    if re.match('^...[^\d]*$', key) != None:
                        info['cases'][key] = value
                    # and the ones with the fitting number at the end
                    else: 
                        try:
                            if re.match('^....*(\d).*$',key).group(1) == str(j + 1):
                                info['cases'][key] = value
                        except:
                            pass
            # the rest is for the alternatives
            alternatives = alternatives[1:]
            if config.debug_lvl > 0: print('SPLITTING of info with Wortart result: ' + str(alternatives) + ' and gender ' + genders)

            # if there are several genders, make a copy of the original, but with different gender 
            for gender in genders[1:]:
                new_word_name = word + ' XALTERNATIVEX ' + ' gender ' + gender
                words[wordsort][new_word_name] = copy.deepcopy(info)
                words[wordsort][new_word_name]['gender'] = gender
                # overwrite cases
                words[wordsort][new_word_name]['cases'] = {}
                for key, value in orig_cases.items():
                    # keep the general ones (without the number at the end)
                    if re.match('^...[^\d]*$', key) != None:
                        words[wordsort][new_word_name]['cases'][key] = value
                    # and the ones with the fitting number at the end
                    else: 
                        try:
                            if re.match('^....*(\d).*$',key).group(1) == str(j + 1):
                                words[wordsort][new_word_name]['cases'][key] = value
                        except:
                            pass

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
                        new_word_name = word + ' XALTERNATIVEX ' + str(i) + ' gender ' + gender
                        words[alt_wordsort][new_word_name] = copy.deepcopy(info)
                        words[alt_wordsort][new_word_name]['info'] = alt
                        words[alt_wordsort][new_word_name]['gender'] = gender
                        # overwrite case values
                        words[alt_wordsort][new_word_name]['cases'] = {}
                        for key, value in orig_cases.items():
                            # keep the general ones (without the number at the end)
                            if re.match('^...[^\d]*$', key) != None:
                                words[alt_wordsort][new_word_name]['cases'][key] = value
                            # and the ones with the fitting number at the end
                            else: 
                                try:
                                    if re.match('^....*(\d).*$',key).group(1) == str(j + 1):
                                        words[alt_wordsort][new_word_name]['cases'][key] = value
                                except:
                                    pass
                else:
                    words[alt_wordsort][word + ' XALTERNATIVEX ' + str(i)] = copy.deepcopy(info)
                    words[alt_wordsort][new_word_name]['info'] = alt
            # if created_alt:
            #    del(words[wordsort][word])


    for wordsort, wds in words.items():
        match = extract_wordsort.match(wordsort) # TODO: test if unicode compatible (vs. python string)
        # here you could only specific wordsorts
        if match == None:
            if config.debug_lvl > 0: print("no wordsort match, jump to next (wordsort was '" + wordsort + "')")
            matched_wordsort = None
            del(words[wordsort])
            continue
        else:
            matched_wordsort = match.group(1)
            if config.debug_lvl > 0: print('matched wordsort is "' + matched_wordsort + '"')

        for word, info in wds.items():
            for case, caseValues in info['cases'].items():
                if type(caseValues) != list:
                    caseValues = [caseValues]
                new_caseValues = []
                for caseValue in caseValues:
                    ### first remove some html snippets and other always disturbing things
                    caseValue = re.sub("&lt;\/?small&gt;", "", caseValue)
                    caseValue = re.sub("&lt;br&gt;", "", caseValue)
                    caseValue = re.sub("\xe2\x80\x99", "", caseValue) # removes ´
                    # replace german 'ß' with 'ss'
                    # caseValue = re.sub('ß', 'ss', caseValue) # NOTE: should be done in fst

                    # replace '-' with nothing e.g. 'x-beinig' becomes 'xbeinig'
                    caseValue = re.sub('-', '', caseValue)
                    # if there are parenthesis with content >= 6, kill dem # TODO: review this heuristic
                    caseValue = re.sub("\(.{6,}\)", "", caseValue)

                    # pre cleanup
                    caseValue = general_cleanup_pre.match(caseValue).group(1)
                    # check if entry is deletable
                    if caseValue == "\xe2\x80\x94": #== "\u2014" == "—": # TODO: check if this works # TODO: could also be defined above
                        if config.debug_lvl > 2: print "found strange Spiegelstrich, kill!"
                        continue

                    # handle alternative cases sometimes given. Split it into a list.
                    # - e.g. 'krabbl(e)'. 
                    # - sometimes also given like this: 'krabbl / krabble'
                    match = regex_alt_parenthesis.match(caseValue)
                    if match != None:
                        caseValue_list = []
                        caseValue_list.append(re.sub('\(|\)', '', caseValue))  # just remove parenthesis
                        caseValue_list.append(re.sub('\(.*\)', '', caseValue)) # remove parenthesis with content
                        caseValue = caseValue_list
                    else:
                        caseValue = [caseValue]
                    # NOTE: !!! from here on, all casevalues are lists of strings !!! 
                    # NOTE: !!
                    # NOTE: !

                    # split alternatives if there is a '<br />'
                    new_casevalue = []
                    for casev in caseValue:
                        new_casevalue += casev.split("&lt;br /&gt;") 
                    caseValue = new_casevalue
                    new_casevalue = []
                    for casev in caseValue:
                        new_casevalue += casev.split("&lt;\/br&gt;") #TODO: CHECKBF verstümmeln 
                    caseValue = new_casevalue


                    # wordsort specific cleanup

                    if matched_wordsort in wordsort_cleanup.keys():
                        new_casevalue = []
                        for casev in caseValue:
                            match_group_nr = wordsort_cleanup[matched_wordsort][1]
                            match = re.match(wordsort_cleanup[matched_wordsort][0], casev)
                            new_casevalue.append(match.group(match_group_nr))
                        caseValue = new_casevalue

                    # post cleanup
                    new_casevalue = []
                    for casev in caseValue:
                        new_casevalue.append(general_cleanup_post.match(casev).group(1))
                    caseValue = new_casevalue
                    new_caseValues += caseValue
                # filter empty strings and double entries
                caseValues = list(set(filter(lambda x: x != "", new_caseValues)))
                # if empty, kill it
                if caseValues == []: 
                    del(info['cases'][case])
                    continue
                else: # save it
                    info['cases'][case] = caseValues

    return words

# picks a random word
def pickWord(words, wordsort=None):
    if wordsort != None:
        rand_wordsort = wordsort
    else:
        rand_wordsort = sample(words.keys(), 1)[0]
    print("Wordsort:", rand_wordsort)
    return sample(words[rand_wordsort].values(), 1)[0]

# this function calls the essential other functions
# @words: is a dictionary created by 'extractFromWikidump' or such loaded by 'loadYaml'
# better name
# NOTE: this function can be seen as an example in which order to call the essential functions
def doAll(words):
    # first clean the words from unnecassary stuff
    print "## do cleanup of cases"
    words = cleanCasesAndSplit(words) #NOTE:from here on, all casevalues are lists of strings (even when only 1 string)
    # extract the smor features
    print "## extract smor features"
    words = extractSmorFeatures(words)
    print "## guess inflectional classes"
    results = generateInflectClasses(words)
    print "## fill hypothesis into words dict"
    # NOTE: a result has the structure [<wordsort>, <word>, <wordinfos enriched with possible hypothesis>]
    for result in results:
        words[result[0]][result[1]] = result[2]
    return words


# statistical output of inflectional classes
# TODO: make return value, describe it and do it the same way as morphisto stats
def statsInflectionalClasses(words):
    stats = dict()
    for wordsort, wds in words.items():
        print "### '"+ wordsort +"' inflectional class counts for (total: " + str(len(wds)) + ")"
        counts = defaultdict(int)
        nr_identified = 0 # nr of words only ONE inflectional class was found in the end
        for word, info in wds.items():
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
        print "IDENTIFIED:", nr_identified, "(thats " + str(nr_identified*1.0/len(wds)) + ")"
        for key in sorted(counts, key=counts.get, reverse=True):
            print "'" + key + "'", " => ", counts[key]
    return stats

# @stats: output from statsInflectionalClasses or statsMorphisto...
def statsPrintPretty(stats, onlyIdentified=True, output_file=None):
    output_string = ''
    for wordsort, counts in stats.items():
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
    for wordsort, wds in words.items():
        for word, info in wds.items():
            # be sure it's no default dict (with unpickable functions in it)
            info = mapToDict(info)
            # bundle job. a job consists of the wordsort, the word, and the informations about it
            job = [wordsort, word, info]
            # add to work queue
            work_queue.put(job)
    if config.debug_lvl > 0: print("########## loaded jobs into work queue. There are #" + str(work_queue.qsize()) + " jobs.")

    # 2. create workers and let them work
    workers = []
    for i in range(config.num_processes):
        if config.debug_lvl > 0: print("initialize worker")
        workers.append(Worker(work_queue, result_queue))

    for worker in workers:
        if config.debug_lvl > 0: print("start worker")
        worker.start()
    
    # 3. gather results and write them into the words dict
    # collect the results off the queue
    results = []
    print("#### Wait till all jobs are done (#" + str(work_queue.qsize()) + ")")
    while (work_queue.empty() == False) or (result_queue.empty() == False) or (len(filter(lambda x: x == True, [w.is_alive() for w in workers] )) > 1): # TODO: and wait till are workers are dead!! one always keeps alive
        if (work_queue.empty() == True) and (result_queue.empty() == True): 
            print( "there are still #" +  str( len(filter(lambda x: x == True, [w.is_alive() for w in workers] ))) + " workers alive, wait till return")
        try:
            # print("waiting for result")
            a_result = result_queue.get()
            # print("Result:", a_result)
            results.append(a_result)
        except:
            if config.debug_lvl > 0: print("something went wrong while moving a result from the result queue to the results list")
            pass
    print("all jobs are done")
    return results

# this function dumps the fully analysed words like the opensource morphology lexicon morphisto
# e.g.
# <BaseStem>
#   <Lemma>Carabinieri</Lemma>
#   <Stem>Carabinieri</Stem>
#   <Pos>NN</Pos>
#   <Origin>fremd</Origin>
#   <InfClass>NMasc_s_s</InfClass>
#   <Frequency>16</Frequency>
# </BaseStem>
# NOTE: only words get dumped which could be assigned to ONE inflectional class, all others will be ignored
def dumpMorphistoLike(words, filename=None):
    if filename == None:
        filename = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + "_morphisto_like" + ".xml"
    outfile = open(filename,'w')
    lines_to_write = []
    lines_to_write.append('<?xml version="1.0" encoding="utf-8"?>\n')
    lines_to_write.append('<?xml-stylesheet type="text/xsl" href="lexicon-transform.xslt"?>\n')
    lines_to_write.append("<smor>\n")
    outfile.writelines(lines_to_write)
    # allowed wordforms. only these word sorts will be written into the file
    # allowed_wordsorts = ['Substantiv', 'Verb', 'Adjektiv']
    for wordsort, wds in words.items():

        # if wordsort in allowed_wordsorts :
        #     pass # thats ok , go on 
        # else: # not allowed, next please
        #    continue # go to next wordsort

        for word, info in wds.items():
            # a list of hypothesis
            try:
                inflectClass = info['inflectionalClasses']
            except:
                continue
            if inflectClass == None:
                continue # go to next word
            if info["pos"] == None:
                continue # go to next word if no pos given
            if len(inflectClass) != 1: # there should only be ONE infl class
                continue # go to next word
            inflectClass = inflectClass[0]
            # only if it it is a real class go on
            if inflectClass == None or inflectClass == '' or inflectClass == '(None found)':
                continue # go to next word
            if info["stem"] == None:
                continue # go to next word 
            # when we are here it's only ONE and a REAL inflectional class
            lines_to_write = []
            lines_to_write.append("\t<BaseStem>\n")
            try:
                if info["pos"] == 'V' and info["ge"] == True:
                    lines_to_write.append("\t\t<MorphMarker>ge</MorphMarker>\n")
            except:
                pass
            lines_to_write.append("\t\t<Lemma>"+info["lemma"]+"</Lemma>\n")
            lines_to_write.append("\t\t<Stem>"+info["stem"]+"</Stem>\n")
            lines_to_write.append("\t\t<Pos>"+info["pos"]+"</Pos>\n")
            lines_to_write.append("\t\t<Origin>nativ</Origin>\n") # TODO: 'nativ' hardcoded
            lines_to_write.append("\t\t<InfClass>"+inflectClass+"</InfClass>\n")
            lines_to_write.append("\t\t<Frequency>0</Frequency>\n") # TODO: '0' hardcoded
            lines_to_write.append("\t</BaseStem>\n")
            outfile.writelines(lines_to_write)
    lines_to_write = []
    lines_to_write.append("</smor>")
    outfile.writelines(lines_to_write)
    outfile.close

# this function returns statistical data evaluated upon the opensource morphisto korpus
# => http://www1.ids-mannheim.de/lexik/home/lexikprojekte/lexiktextgrid/morphisto.html
# TODO: describe return value
# TODO: do it the same way like the stats function
def statsMorphisto(pathToMorphistoXml=None):
    if pathToMorphistoXml == None:
        # try it in config
        if config.pathToMorphistoXml != None:
            pathToMorphistoXml = config.pathToMorphistoXml
        else:
            print("no path could be found to morphisto xml")
            return None
    print("Using '" + pathToMorphistoXml + "'")
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
        self.kill_received = False
        self.fst_analyser = None
        self.regex_nouns_singular = re.compile("^(.*?)(_.*?)?(_.*)?$") # TODO: move to regex file
        # if a mapping of nouns with only singular cases happens, the following list will be used to check, if the mapped class is legit
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
        self.static_infl_class = {
            "Abkürzung"                : "ABK", # Wiktionary is underspecified (SMOR treats abbreviation as features, but gives original part-of-speech/analysis
            "Adverb"                    : "Adv",
            "Partikel"         		        : "Adv",
            "Fokuspartikel"         		: "Adv",
            "Gradpartikel"          		: "Adv",
            "Interrogativadverb"    		: "WAdv",
            "Konjunktionaladverb"   		: "Adv",
            "Lokaladverb"           		: "Adv",
            "Pronominaladverb"      		: "ProAdv",
            "Temporaladverb"        		: "Adv",
            "Konjunktion"               : "Konj-Kon",
            "Subjunktion"               : "Konj-Sub",
            "Vergleichspartikel"        : "Konj-Vgl",
            "Interjektion"              : "Intj",
            "Grußwort"              		: "Intj",
            "Grußformel"            		: "Intj",
            "Onomatopoetikum"       		: "Intj",
            "Antwortpartikel"           : "Ptkl-Ant",
            "Negationspartikel"         : "Ptkl-Neg"
            # TODO: Numerale ?
        }

    def run(self):
        while not self.kill_received:
            # get a task
            if config.debug_lvl > -1: print("a worker wants to get a job (one of #" + str(self.work_queue.qsize()) + " left)")
            try:
                job = self.work_queue.get_nowait()
            except Exception as e:
                if config.debug_lvl > 0: print("Unexpected error:", sys.exc_info()[0], "\n", e) # queue.Empty
                if self.work_queue.qsize() == 0:
                    if config.debug_lvl > 0: print("The work queue really is empty! destroy worker")
                    break
                else:
                    if config.debug_lvl > 0: print("There are still jobs in the queue, back to work!")
                    continue # go back to top of while loop
            if config.debug_lvl > 1: print("worker gotta job => " + str(job))
            word_sort = job[0]
            word_infos = job[2]
 
            # the actual processing
            # check if static infl class mapping is there
            if word_sort in self.static_infl_class.keys(): # TODO: check if ok for utf-8
                mapped_static_infl_class = self.static_infl_class[word_sort] 
                # insert the found static infl class into the word_information
                word_infos['inflectionalClasses'] = [mapped_static_infl_class]
                job[2] = word_infos
                # store the result
                if config.debug_lvl > 0: print("a worker got a job (#" + str(self.work_queue.qsize()) + " jobs left) (pos is:" + str(word_infos['pos']) +") => static map to: " + mapped_static_infl_class)
                self.result_queue.put(job)
                continue # go back to top of while loop
            
            try:
                if len(re.findall('Nachname', word_infos['info'])) > 0:
                    if word_infos['lemma'][-1] == 's' or word_infos['lemma'][-1] == 'z':
                        word_infos['inflectionalClasses'] = ['FamName_s']
                    else:
                        word_infos['inflectionalClasses'] = ['FamName_0']
                    job[2] = word_infos
                    # store the result
                    if config.debug_lvl > 0: print("a worker got a job (#" + str(self.work_queue.qsize()) + " jobs left) (pos is:" + str(word_infos['pos']) +") => static map to: " + 'AdjPos')
                    self.result_queue.put(job)
                    continue # go back to top of while loop
            except:
                pass

            # special case only positive adjective # TODO: test CHECKBF
            if word_infos['pos'] == 'ADJ' and len(word_infos['cases']) == 1 and word_infos['cases'].keys()[0] == 'Positiv':
                word_infos['inflectionalClasses'] = ['AdjPos']
                job[2] = word_infos
                # store the result
                if config.debug_lvl > 0: print("a worker got a job (#" + str(self.work_queue.qsize()) + " jobs left) (pos is:" + str(word_infos['pos']) +") => static map to: " + 'AdjPos')
                self.result_queue.put(job)
                continue # go back to top of while loop


            if config.debug_lvl > 0: print("a worker got a job (#" + str(self.work_queue.qsize()) + " jobs left) (pos is:" + str(word_infos['pos']) +")")
            # when no static mapping could be found, actually analyse it
            if self.fst_analyser == None:
                self.fst_analyser = FstWrapper() 
            if config.debug_lvl > 1: print("child is alive? " + str(self.fst_analyser.child.isalive()) + ", Terminated? " + str(self.fst_analyser.child.terminated))
            hypothesis = self.generateHypothesis(word_infos) ######################## HERE the hypothesis gets generated
            original_hypothesis = copy.deepcopy(hypothesis) # we can fallback to this, if we filter too much

            # nouns only allow '..._x' interpretations if ALL case values are the same and otherwise
            set_of_case_values = set([item for sublist in word_infos['cases'].values() for item in sublist])
            if not len(set_of_case_values) == 1 and hypothesis != None:
                is_s_x = False
                # Genitiv can have a 's' at the end
                set_of_case_values_without_gen = set([y for x in filter(lambda x: x[0] != 'Genitiv Singular', word_infos['cases'].items()) for y in x[1]]) 
                if len(set_of_case_values_without_gen) == 1 and len(set_of_case_values) == 2 and 'Genitiv Singular' in word_infos['cases'].keys() and len(word_infos['cases']['Genitiv Singular']) == 1:
                    # if this is the case there is a chance that is  a _s_x. That means that all forms are the same expect the genitiv singular has a 's' at the end
                    gen_sing = word_infos['cases']['Genitiv Singular'][0]
                    if gen_sing[-1:] == 's' and set([gen_sing, gen_sing[:-1]]) == set_of_case_values:
                        hypothesis = filter(lambda x: x[-3:] == 's_x', hypothesis)
                        is_s_x = True
                if not is_s_x:
                    hypothesis = filter(lambda x: x[-2:] != '_x', hypothesis)
            elif len(set_of_case_values) == 1 and hypothesis != None:
                hypothesis = filter(lambda x: x[-3:] == '0_x', hypothesis)


            #### post processing of hypothesis
            # special case for Nouns: if there are only singuar cases, then map the inflectional classes
            # print("Post processing of hypothesis.  (wordsort is: " , word_infos['pos']) # TODO: this is a debug print
            if word_infos['pos'] == "NN":
                # print("Special rule for Nouns, check if only singular cases!") # TODO: this is a debug print
                only_singular = True
                for casename, casesmorfeatures in word_infos['smor_features'].items():
                    if not ('<Sg>' in casesmorfeatures):
                        only_singular = False
                        break # stops inner for loop
                if (only_singular == True) : 
                    # when there are only singular cases map the inflectional classes to a SingularClass or a Nameclass 
                    if config.debug_lvl > 0: print(">>>>>>>>>>>>> a noun with NO PLURAL forms was detected, map inflectional classes") # TODO: this is debug info
                    mapped_hypothesis = []
                    if word_infos['info'] and 0 < len(re.findall('Eigenname|Vorname|Nachname|Toponym', word_infos['info'])):
                        # map to name class
                        for hypo in (hypothesis or []) :
                            match = self.regex_nouns_singular.match(hypo)
                            gender = match.group(1)[1:]
                            name_infl_class = 'Name-' + gender + (match.group(2) or "") # TODO: test singular noun fix CHECKBF
                            # filter arising inflClasses not all are possible
                            if name_infl_class in self.possible_name_classes:
                                mapped_hypothesis.append(name_infl_class)
                            else:
                                if config.debug_lvl > 0: print name_infl_class  + " is  not in " + str(self.possible_name_classes)
                        # readjust pos tag which was changed to NN for analyzing purposes
                        word_infos['pos'] = 'NE' # TODO: ask rico if this is ok

                    else: # map to singular class
                        for hypo in (hypothesis or []) :
                            match = self.regex_nouns_singular.match(hypo)
                            singular_infl_class = match.group(1) + "/Sg" + (match.group(2) or "")
                            singular_infl_class_fallback = match.group(1) + "/Sg" # TODO: test singular noun fix
                            # filter arising inflClasses not all are possible
                            if singular_infl_class in self.possible_singular_infl_classes:
                                mapped_hypothesis.append(singular_infl_class)
                            elif singular_infl_class_fallback in self.possible_singular_infl_classes: # TODO: not sure if this is ok...
                                mapped_hypothesis.append(singular_infl_class_fallback)
                            else:
                                if config.debug_lvl > 0: print singular_infl_class + ' and ' + singular_infl_class_fallback + " are not in " + str(self.possible_singular_infl_classes)
                    mapped_hypothesis = list(set(mapped_hypothesis))
                    if config.debug_lvl > 0: print("mapped classes are: ", mapped_hypothesis)
                    hypothesis = mapped_hypothesis


                # lemma check for count german umlauts # TODO CHECKBF
                lemma_umlaut_count = len(re.findall('ö|ä|ü|Ü|Ä|Ö', word_infos['lemma']))
                more_umlauts_then_lemma = False
                for v in word_infos['cases'].values():
                    for vv in v:
                        if lemma_umlaut_count < len(re.findall('ö|ä|ü|Ü|Ä|Ö', vv)):
                            more_umlauts_then_lemma = True
                            break # break from inner loop
                    if more_umlauts_then_lemma: break # break from inner loop
                if hypothesis and more_umlauts_then_lemma:
                    # only keep hypothesis which contain '$'. this stands for a change from a vowel to an umlaut in plural
                    hypothesis = filter(lambda x: '$' in x, hypothesis)
                elif hypothesis != None: # do the opposite
                    # only keep hypothesis which contain '$'. this stands for a change from a vowel to an umlaut in plural
                    hypothesis = filter(lambda x: not '$' in x, hypothesis)

                # special case _es and _s Genitiv. only take _es if there is at least one casevalue which has the ending 'es'
                if hypothesis != None and len(hypothesis) == 2 and set(hypothesis) in [set(l) for l in [['NMasc_es_e','NMasc_s_e'],['NNeut_es_e','NNeut_s_e'],['NMasc/Sg_es','NMasc/Sg_s'],['NNeut/Sg_es','NNeut/Sg_s']]]:
                    es_case = False
                    for casename in word_infos['cases'].keys():
                        if 'Genitiv' in casename:
                            for casev in word_infos['cases'][casename]:
                                if casev[-2:] == 'es':
                                    es_case = True
                                    break # break from inner for
                        if es_case: break # break also this for loop
                    if es_case and hypothesis != None: # if true only keep the '_es' hypothesis 
                        hypothesis = filter(lambda x: '_es' in x, hypothesis)
                        # print( ' ########### _es _s desambiguation: _ES WINS ' )
                    elif hypothesis != None: # do the opposite 
                        hypothesis = filter(lambda x: '_s' in x, hypothesis)
                        # print( ' ########### _es _s desambiguation: _S WINS ' )

            elif word_infos['pos'] == 'V':
                # NOTE: special case for Verbs. if there are only the analysis VVReg-el/er and VVReg, they can be desambiguiated by the ending
                if len(hypothesis or []) == 2 and ("VVReg-el/er" in (hypothesis or [])) and ("VVReg" in (hypothesis or [])):
                    word = job[1][0]
                    word_end = word[len(word_infos['stem']):]
                    if word_end == 'en':
                        if config.debug_lvl > 0: print("Special case verb: desambiguate VVReg vs. VVReg-el/er => VVReg wins")
                        hypothesis = ['VVReg']
                    else:
                        if config.debug_lvl > 0: print("Special case verb: desambiguate VVReg vs. VVReg-el/er => VVReg-el/er wins")
                        hypothesis = ['VVReg-el/er'] 

            # insert the generated hypothesis into the word_information
            if hypothesis == None:
                hypothesis = []
            if original_hypothesis == None:
                original_hypothesis = []
            if hypothesis != []:
                word_infos['inflectionalClasses'] = hypothesis
            else: # fallback to original generated hypothesis when there is no hypothesis left after all the filtering TODO: eventuelly not the best way 
                word_infos['inflectionalClasses'] = original_hypothesis

            job[2] = word_infos
            # store the result
            self.result_queue.put(job)

    # NOTE: the name of this function is kind of misleading cause the ANALYSE method of the fst_wrapper is used
    # precondition: smor symbols must be generated before
    def generateHypothesis(self, word):
        # first hardcoded special cases NOTE: hardcoded
        if word['pos'] == 'ADJ':
            regex_superlativ_e = re.compile(".*esten$") # TODO: does not work for german double 's' like in 'größten' 
            regex_superlativ = re.compile(".*sten$")    # TODO: does not work for german double 's' like in 'größten'
            if word['stem'][-1] == 'e':
                # NOTE: when the adjective ends with 'e' it always will be Adj+
                return ["Adj+"]
            try:
                if len(word['cases']['Superlativ']) == 1:
                    if regex_superlativ_e.match(word['cases']['Superlativ'][0]) != None:
                        return ["Adj+e"] 
                    elif regex_superlativ.match(word['cases']['Superlativ'][0]) != None:
                        return ["Adj+"]
                elif len(word['cases']['Superlativ']) == 2:
                    matched_sup_e = False
                    matched_sup = False 
                    for sup in word['cases']['Superlativ']:
                        if regex_superlativ_e.match(word['cases']['Superlativ'][0]) != None:
                            matched_sup_e = True 
                        elif regex_superlativ.match(word['cases']['Superlativ'][0]) != None:
                            matched_sup = True 
                    if matched_sup_e and matched_sup:
                        return ["Adj+(e)"]
            except:
                pass

        # now the generic part
        caseInflectClasses = [] # a list of sets
        word['analysed_as'] = defaultdict(list)
        word['analysed_as']['pos for analysation'] = word['pos']
        for caseName, caseValue in word['cases'].items():
            caseInflectClass = set()
            for casev in caseValue: # TODO!! look if this is ok (and that below)
                if casev == '':
                    continue # jump to next case
                casev = reformatForAnaly(word, casev, caseName)
                if casev == '':
                    continue # nothing to analyse left, go to next word
                word['analysed_as'][caseName].append(casev)
            caseHypothesis = []
            for casev in word['analysed_as'][caseName]: # TODO!! look if this is ok (and that below)
                try:
                    # NOTE: the fst_tool is in latin-1 !! so encode to latin-1
                    tmp_analysis = self.fst_analyser.analyse(casev) # .decode('utf-8').encode('latin-1'))
                    caseHypothesis += tmp_analysis or [] 
                except (UnicodeEncodeError, UnicodeDecodeError):
                    if config.debug_lvl > 0: print('Exception: could not encode "' + str(casev) + '" to latin-1. ignore it instead')
                    continue # jump to next case
                except Exception as e:
                    if config.debug_lvl > 0: print "Unexpected while trying to use FstWrapper:", sys.exc_info()[0] , e
                    continue

            try:
                stem = word['stem']
                stem_reformat = reformatForAnaly(word, stem, None)
                word['analysed_as']['XstemX'] = stem_reformat
                caseHypothesis = self.fst_analyser.filterAnalysis(caseHypothesis, word['smor_features'][caseName], stem_reformat, word['pos']) # .decode('utf-8').encode("latin-1"), word['pos'])
            except (UnicodeEncodeError, UnicodeDecodeError):
                if config.debug_lvl > 0: print('Exception: could not encode (filtering)"' + str(word['stem']) + '" to latin-1. ignore it instead' + str(word))
                continue # jump to next case
            except Exception as e:
                if config.debug_lvl > 0: print "Unexpected while trying to use FstWrapper (filtering):", sys.exc_info()[0], e, word
                continue # jump to next case

            # after the raw filteringm we go in the other direction and let the fst generate the possible forms. all if this forms must be entries in wiktionary
            new_caseHypothesis = []
            for caseh in caseHypothesis:
                # lemma check here
                if word['pos'] != 'V': #exclude verbs in this check... TODO: it's to complicated with them
                    if word['analysed_as']['XstemX'] + '<' in caseh:
                        pass # that s ok 
                    else:
                        # print('stem ' + word['analysed_as']['XstemX'] + ' is not in analysis ' + caseh)
                        continue # go to next case, stem is not in hypothesis 
                gen_forms = self.fst_analyser.generate(caseh)
                if gen_forms == None:
                    continue # go to next case
                # all generated forms must be found as entries
                good_hypothesis = True
                for gen_form in gen_forms:
                    if gen_form in word['analysed_as'][caseName]:
                        # print("###################### OK  the case hypothesis '" + caseh + "' generated a form, could be found in wiktionary! (" +gen_form+ ")")
                        # print("###################### entries: " + str(word['analysed_as'][caseName]))
                        pass # thats good go on
                    else:
                        # print("###################### NOK  the case hypothesis '" + caseh + "' generated a form, that had no entry in wiktionary! (" +gen_form+ ")")
                        # print("###################### entries: " + str(word['analysed_as'][caseName]))
                        good_hypothesis = False
                        break # break out of inner for loop
                if good_hypothesis: # if the hypothesis still is good, add it to the new_caseHypothesis
                    new_caseHypothesis.append(caseh)
            caseHypothesis = new_caseHypothesis

            # at last we can determine the possible inflectional classes for this case
            # print "CCCCCCCCCCCCCCCCCCCCCASEhypothesis adj of"+str(word["stem"])+ ":" + str(caseHypothesis) # TODO: this is a debug print
            for caseHypo in caseHypothesis:
                inflClass = self.fst_analyser.determineInflClass(caseHypo)
                if inflClass != None:
                    caseInflectClass.add(inflClass)
            if len(caseInflectClass) > 0:
                word['analysed_as'][caseName].append(caseInflectClass)
                caseInflectClasses.append(caseInflectClass)

        # finally produce the intersection of all the sets
        if config.debug_lvl > 1: print(">>>>>>>>>>>>>>>> before insection:" + str(caseInflectClasses))
        word['analysed_as']['XbeforeIntersectionX'] = copy.deepcopy(caseInflectClasses)
        if len(caseInflectClasses) > 1:
            intersection = list(set.intersection(*caseInflectClasses))
            word['analysed_as']['XafterIntersectionX'] = copy.deepcopy(intersection)
            if config.debug_lvl > 1: print "<<<<<<<<<<<<<< Intersection: ", intersection
            if intersection == []: 
                if config.debug_lvl > 0: print("could not find a intersection of these inflectional classes", str(caseInflectClasses)) 
            return intersection 
        elif len(caseInflectClasses) == 1:
            return list(*caseInflectClasses)
        else:
            return None

def reformatForAnaly(word, casev, caseName=None):
    # NOTE: POS dependent word modification just for analysis
    if word['pos'] == 'V':
        if caseName != None and caseName != "Partizip II":
            casev_splitted = casev.split()
            casev = casev_splitted[0]
            if caseName != None and caseName == "Gegenwart_ich":
                if len(casev_splitted) > 1:
                    word['prefix'] = casev_splitted[-1] # must be done like this because there are entries like "mühte mich ab", 'ab' is the prefix
                else:
                    word['prefix'] = ''

                # also try to determine if a 'ge' prefix is additionally used in the partizip of the verb
                if word['cases']['Partizip II'] != None and len(word['cases']['Partizip II']) > 0 :
                    prefix_len = len(word['prefix'])
                    ge_start = 0+prefix_len
                    ge_end = 2+prefix_len
                    pp = word['cases']['Partizip II'][0] # TODO: now we just take the first, but what when there are several possibilities ?
                    ge_1 = pp[ge_start:ge_end]
                    ge_2 = word['stem'][ge_start:ge_end]
                    if config.debug_lvl > 0: print("///////////////////////////// try to analyse if 'ge' is needed for the partizip", pp, word['stem'], word['prefix'], ge_1, ge_2)
                    if (ge_1 == 'ge') and (ge_2 != 'ge'):
                        word['ge'] = True

        else:
            casev = casev.split()[-1]

    if word['pos'] == 'ADJ' or word['pos'] == 'ADV':
        # adjectives & adverbs always should be analysed as lower case words
        casev = string.lower(casev)
    # NOTE: POS INdependent word modification just for analysis
    # NOTE: just for the analysis numbers, '-' and ' ' get  removed
    casev = re.sub("\d","", casev)
    casev = re.sub("-","", casev)
    casev = re.sub(" ","", casev)
    casev = re.sub(",","", casev)
    casev = re.sub("\d","", casev)
    casev = re.sub("\xc2\xad","", casev) # NOTE: it's a little bit longer white space
    casev = re.sub("–","", casev) # NOTE: it's a little bit longer white space
    try:
        if word['pos'] == 'NN':
            casev = string.lower(casev)
            casev = string.capitalize(casev)
        else:
            casev = string.lower(casev)
    except:
        if config.debug_lvl > 0: print("###################################################### failed @ lower / capitalize string")
    return casev

# NOTE: a dict with analysed words is expected as argument (e.g. output of 'doAll' function)
def extractFailedAnalysis(words):
    failed_words = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict())))
    for wordsort, wds in words.items():
        for word, info in wds.items():
            try:
                iC = info['inflectionalClasses']
                if iC == '(None found)' or iC == None or iC == "None" or iC == "" or iC == [] or iC == '(None)':
                    failed_words[wordsort][word] = info
            except KeyError:
                failed_words[wordsort][word] = info
    return failed_words
