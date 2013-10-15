#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright ©2013 University of Zürich
# Author: Beat Kunz <beat.kunz@access.uzh.ch>
from subprocess import call
import os
from collections import defaultdict
import re
import sys
from datetime import datetime
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper, CSafeDumper as SafeDumper
except ImportError:
    print "could not load the faster cloader/cdumper/csafedumper for yaml package.\n will load standard loader/dumper"
    from yaml import Loader, Dumper, SafeDumper

##### set files
benchmark_file_name = 'r7-test.conll'
shell_script_name = 'create_test_output.sh'
analysis_dir = 'testoutput'

##### call bash scripts that generate analysis of 
print('Python calls shell script', shell_script_name, 'with', benchmark_file_name)
call(['sh', shell_script_name, benchmark_file_name])
# print('Python finished calling the shell script')

####### following functions I could reuse from Rico Sennrich's project https://github.com/rsennrich/ParZu/ from the file morphisto2prolog.py

def get_repr(key,d):
    if key in d:
        return "'"+d[key].replace("'",r"\'")+"'"
    else:
        return '_'
def get_repr2(word):
    word = word.replace("\\","\\\\")
    return "'"+word.replace("'",r"\'")+"'"

#get all morphological features from the morphisto output
def extract(line):
    
    d = {}
    
    features = re_any.findall(line)
    
    for feature in features:
        
        if feature in ['Masc','Fem','Neut']:
            d['gender'] = feature
            
        elif feature in ['Sg','Pl']:
            d['number'] = feature
            
        elif feature in ['Nom','Akk','Dat','Gen']:
            d['case'] = feature
        
        elif feature == 'Acc':
            d['case'] = 'Akk'
        
        elif feature in ['Sw','St','St/Mix']:
            d['declension'] = feature
            
        elif feature in ['Pos','Comp','Sup']:
            d['grade'] = feature
            
        elif feature in ['Ind','Konj','Subj']:
            if feature in ['Konj', 'Subj']: # NOTE: this mapping has to be done, because ower testset has only ind and konj
                d['aspect'] = 'Konj'
            else: 
                d['aspect'] = 'Ind'
            
        elif feature in ['1','2','3']:
            d['person'] = feature
            
        elif feature in ['Pres', 'Past']:
            d['tense'] = feature
            
        elif feature in ['Def', 'Indef']:
            d['definiteness'] = feature
            
        elif feature == 'PPres':
            d['derivation'] = '<PPRES'
            
        elif feature == 'PPast':
            d['derivation'] = '<PPAST'
            
    return d


#get stts part_of_speech tag from morphisto output
def get_true_pos(raw_pos,line):
    pos = raw_pos
    pos2 = None
    other = ''

    if raw_pos == 'V': 
    
        #stts tagset distinguishes between VV, VA and VM
        if line.startswith('<CAP>'):
            line = line[5:]
        if line.startswith('haben') or line.startswith('werden') or line.startswith('sein'):
            pos += 'A'
        elif line.startswith('dürfen') or line.startswith('können') or line.startswith('sollen') or line.startswith('müssen') or line.startswith('mögen') or line.startswith('wollen'):
            pos += 'M'     
        else:
            pos += 'V'
        
        #stts tagset distinguishes between VVINF, VVFIN, VVPP and VVIZU
        if '<Inf>' in line:
            if '<zu>' in line:
                pos += 'IZU'
            else:
                pos += 'INF'
        elif '<PPast>' in line:
            pos += 'PP'
        elif '<Ind>' in line or '<Konj>' in line or '<Subj>' in line:
            pos += 'FIN'
            
        elif '<Imp>' in line:
            pos += 'IMP'
            
        elif '<PPres>' in line:
            pos = 'ADJD'
            
        else:
            sys.stderr.write('FIN or INF or PP?: '+line+'\n')
    
    #distinction between ADJA and ADJD
    elif raw_pos == 'ADJ':
        if '<Pred>' in line or '<Adv>' in line:
            pos += 'D'
        else:
            pos += 'A'
    
    #map pronouns to stts tagset
    elif pos in ['PD','PI','PP','PREL','PW','PPOS']:
        
        if '<pro>' in line or '<Pro>' in line:
            if pos == 'PI' and ('<mD>' in line or '<Invar>' in line):
                pos2 = pos + 'DAT'
            else:
                pos2 = pos + 'AT'
            pos += 'S'
        elif '<subst>' in line or '<Subst>' in line:
            pos += 'S'
        else:
            if pos == 'PI' and ('<mD>' in line or '<Invar>' in line):
                pos += 'DAT'
            else:
                pos += 'AT'
           
    elif raw_pos == 'KONJ' or raw_pos == 'CONJ':
        if '<Vgl>' in line or '<Compar>' in line:
            pos = 'KOKOM'
        elif '<Inf>' in line:
            pos = 'KOUI'
        elif '<Sub>' in line:
            pos = 'KOUS'
        elif '<Kon>' in line or '<Coord>' in line:
            pos = 'KON'
            
    elif raw_pos == 'PTKL' or raw_pos == 'PTCL':
        if '<Ant>' in line or '<Ans>' in line:
            pos = 'PTKANT'
        elif '<Neg>' in line:
            pos = 'PTKNEG'
        elif '<zu>' in line:
            pos = 'PTKZU'
        elif '<Adj>' in line:
            pos = 'PTKA'
        elif '<Vz>' in line:
            pos = 'PTKVZ'
          
    elif pos == 'PPER':
        if '<refl>' in line or '<Refl>' in line:
            pos = 'PRF'
        elif '<prfl>' in line or '<Prfl>' in line:
            pos = 'PRF'
            pos2 = 'PPER'
            
    elif pos == 'PUNCT' or pos == 'IP':
        if '<Left>' in line or '<Right>' in line or '<links>' in line or '<rechts>' in line:
            pos = '$('
        elif '<Norm>' in line:
            pos = '$.'
        elif '<Comma>' in line or '<Komma>' in line:
            pos = '$,'

    return pos,pos2


#longest common subsequence code from http://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Longest_common_subsequence
def LCS(X, Y):
    m = len(X)
    n = len(Y)
    # An (m+1) times (n+1) matrix
    C = [[0] * (n+1) for i in range(m+1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            if X[i-1] == Y[j-1]:
                C[i][j] = C[i-1][j-1] + 1
            else:
                C[i][j] = max(C[i][j-1], C[i-1][j])
    return C

def backTrack(C, X, Y, i, j):
    if i == 0 or j == 0:
        return ()
    elif X[i-1] == Y[j-1]:
        return backTrack(C, X, Y, i-1, j-1) + (i-1,)
    else:
        if C[i][j-1] < C[i-1][j]:
            return backTrack(C, X, Y, i-1, j)
        else:
            return backTrack(C, X, Y, i, j-1)
def getlemma(line,word,pos):

    if pos == 'NN':
    #sadly complicated hack to get desired lemmata for nouns. Morphisto normalizes all morphemes in the stem, which we don't want.
    #using longest common subsequence matching to find boundary, taking normalized last_morpheme, unnormalized stem.
        last_morpheme = re_last.search(line)

        if not last_morpheme:
            return re_any.sub('',line)

        last_morpheme = last_morpheme.group(1)
        word_lc = word.lower()
        last_morpheme_lc = last_morpheme.lower()
        try:
            joinpoint = backTrack(LCS(word_lc,last_morpheme_lc),word_lc,last_morpheme_lc,len(word_lc),len(last_morpheme_lc))[0]
        except IndexError:
            lemma = re_any.sub('',line)
            try:
                return lemma[0] + lemma[1:].lower()
            except IndexError:
                return lemma
        if joinpoint > 1:
            if word[joinpoint-1] == '-':
                return re_any.sub('',word[:joinpoint])+last_morpheme
            else:
                return re_any.sub('',word[:joinpoint])+last_morpheme_lc
        else:
            return last_morpheme
    
    lemma = re_any.sub('',line) #delete all markup, leaving what we'll use as lemma


    #SMOR gives the same lemma to er/sie/es; keep the distinction in ParZu
    #(this is slightly redundant, since we can get the same info from the gender, but the grammar looks at the lemma to find cases of expletive 'es')
    if lemma == 'sie':
        if '<3><Sg><Neut>' in line:
            lemma = 'es'
        elif '<3><Sg><Masc>' in line:
            lemma = 'er'
        elif '<1><Sg>' in line:
            lemma = 'ich'
        elif '<2><Sg>' in line:
            lemma = 'du'
        elif '<1><Pl>' in line:
            lemma = 'wir'
        elif '<2><Pl>' in line:
            lemma = 'ihr'

    try:
        return lemma[0] + lemma[1:].lower()
    except IndexError:
        return lemma

#### END functions


##### load benchmark ( / Gold-Daten ) and map grammatical analysis tags
# load
benchmark_file = open(benchmark_file_name)

benchmark_dict = defaultdict(list)
for line in benchmark_file:
    # check if empty line
    if re.match('^$', line) != None:
        continue # go to next line
    #splitted_line = filter(lambda x: x != '', line.split("\t"))
    line = line.rstrip()
    splitted_line = line.split("\t")
    # print("Splitted line looks like this:", splitted_line)
    if len(splitted_line) < 6:
        # print( "entry had not enough rows", splitted_line)
        continue
    word = splitted_line[1]
    word_lemma = splitted_line[2]
    word_pos = splitted_line[4]
    word_morph = splitted_line[5]
    # TODO: map morphological infos
    mapped_word_morph = {}
    word_morph += "******" # NOTE: cheap solution, so that there are always enough symbols
    # morph info for adjectives and nouns
    if word_pos == 'NN' or word_pos == 'ADJ':
        # case information
        if 'a' == word_morph[0]:
            mapped_word_morph['case'] = 'Akk'
        elif 'g' == word_morph[0]:
            mapped_word_morph['case'] = 'Gen'
        elif 'd' == word_morph[0]:
            mapped_word_morph['case'] = 'Dat'
        elif 'n' == word_morph[0]:
            mapped_word_morph['case'] = 'Nom'
        # gender information
        if 'm' == word_morph[3]:
            mapped_word_morph['gender'] = 'Masc'
        elif 'f' == word_morph[3]:
            mapped_word_morph['gender'] = 'Fem'
        elif 'n' == word_morph[3]:
            mapped_word_morph['gender'] = 'Neut'
    elif word_pos == 'V':
        # person information
        if '1' == word_morph[0]:
            mapped_word_morph['person'] = '1'
        elif '2' == word_morph[0]:
            mapped_word_morph['person'] = '2'
        elif '3' == word_morph[0]:
            mapped_word_morph['person'] = '3'
        # mood information
        if 'i' == word_morph[2]:
            mapped_word_morph['aspect'] = 'Ind'
        elif 'k' == word_morph[2]:
            mapped_word_morph['aspect'] = 'Konj'
        # tense information
        if 's' == word_morph[3]:
            mapped_word_morph['tense'] = 'Pres'
        elif 't' == word_morph[3]:
            mapped_word_morph['tense'] = 'Past'
    # number information for all wordsorts
    if 's' == word_morph[1]:
        mapped_word_morph['number'] = 'Sg'
    elif 'p' == word_morph[1]:
        mapped_word_morph['number'] = 'Pl'
    # print("Mapped_word_morph:", mapped_word_morph)

    word_data = {'lemma': word_lemma, 'pos': word_pos, 'morph': mapped_word_morph}
    benchmark_dict[word].append(word_data)

## END of function imported from morphisto2prolog script

# NOTE: this function is from a forum http://mail.python.org/pipermail/tutor/2009-October/072483.html
def mapToDict(d):
    """recursively convert defaultdicts into regular dicts"""
    d = dict(d)
    d.update((k, mapToDict(v)) for k,v in d.items() if isinstance(v, defaultdict))
    return d

# NOTE: automatically transforms defaultdicts to dicts 
def dumpYaml(words, filename=None):
    #if config.debug_lvl == 0:
    print  "dump into yaml file (this could take a while)"
    if filename == None:
        filename = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + "_eval_results" + ".yaml"
    stream = file(filename,'w')
    yaml.dump(mapToDict(words), stream, Dumper=Dumper, allow_unicode=True)
    # yaml.safe_dump(mapToDict(words), stream=stream, allow_unicode=True) # TODO: makes yaml unloadable

# extract lemma and pos
# map taggs. tags to map: for nouns and adjectives => kasus / numerus / genus, for verbs => person / numerus / mood / tense

##### load different analysis into dict (dictionary build like this: diff_analysis['<analysis_type>']['<word>'] = [[<word1analysis1>, <word1analysis2>, ...], [<word2analysis1>, <word2analysis2>, ...] ])
diff_analysis = {}

re_mainclass = re.compile('<\+(.*?)>')
re_any = re.compile('<(.*?)>')
re_segment = re.compile('<([A-Z]*?)>')
re_last = re.compile('(?:^|\W)([\w\.]+?)(?:<[\w\-\^]*>)*?<\+',re.UNICODE)
limit = 100
for filename in os.listdir(analysis_dir):
    nr = 0
    #print("loading testouput: " + filename)
    diff_analysis[filename] = defaultdict(list)
    testoutput_file = open(analysis_dir + "/" + filename)
    word_analysis = None
    for line in testoutput_file:
        lemma = ''
        pos = ''
        morph = []
        other = "''"
        
        line = line.rstrip()

        if line.startswith('> ') or line == '>':
            if word_analysis != None:
                diff_analysis[filename][word].append(word_analysis)
                # print("WORD ANALYSIS added:", word, word_analysis)
                nr += 1
                #if nr >= limit: # TODO: remove, just for testing with fewer words
                #    break
            # reset word_analysis list
            word_analysis = []
            word = line[2:]
            continue

        elif line.startswith('no result'):
            # reset word_analysis list
            word_analysis = []
            # print("gertwol({0},'<unknown>',_,_,_).".format(get_repr2(word)))
            continue

        elif line.startswith('><+') or line.startswith('<<+'):
            # reset word_analysis list
            word_analysis = []
            # print("gertwol({0},{0},'$(',_,'').".format(get_repr2(line[0])))
            continue

        try:
            raw_pos = re_mainclass.search(line).group(1)
        except:
            sys.stderr.write(line)
            raise

        pos,pos2 = get_true_pos(raw_pos,line)
               
        extracted_morph = extract(line)

        lemma = getlemma(line,word,pos)
        
        if 'derivation' in extracted_morph:
            other = get_repr('derivation',extracted_morph)
        ana = {'pos': pos, 'morph': extracted_morph, 'lemma': lemma}
        # print("Morph extracted:", ana['morph'])
        word_analysis.append(ana)

        if pos2:
            ana = {'pos': pos2, 'morph': extracted_morph, 'lemma': lemma}
            # print("Morph extracted:", ana['morph'])
            word_analysis.append(ana)
    testoutput_file.close()
    # print("Finished loading:", diff_analysis[filename])
    # print("let's print the loaded analysis of " + filename )

results = defaultdict(lambda: defaultdict(int))
# and differentiated by pos
results_pos = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

for benchmark_word, word_info in benchmark_dict.items():
    word_info = word_info[0] # TODO: change this.
    for transducername, twords in diff_analysis.items():
        try:
            word_info_anas = twords[benchmark_word]
        except:
            # print("########### could not find word analysis for benchmark_word" + benchmark_word)
            results[transducername]['fail not found in dict'] += 1
            results_pos[transducername][word_info['pos']]['fail not found in dict'] += 1
            continue # next transducer's proposals for this benchmark word
        found_correct_lemma_and_pos = False
        found_correct_lemma_and_pos_and_morph = False
        # print("Word_info_anas", word_info_anas)
        for ana_list in word_info_anas:
            for ana in ana_list:
                # print("Ana:", ana)
                # print("Benchmark:", word_info)
                if word_info['lemma'] == ana['lemma'] and word_info['pos'] == ana['pos']:
                    found_correct_lemma_and_pos = True
                    all_morph_correct = True  # NOTE: this stays only true if all morphological information given by the benchmark word can be found in the analysis
                    for morph_name, morph_value in word_info['morph'].items():
                        try:
                            if morph_value != ana['morph'][morph_name]:
                                all_morph_correct = False
                                break # from inner loop
                        except:
                            # if it could not be found it's also a fail 
                            all_morph_correct = False
                            break # from inner loop
                            
                    if all_morph_correct:
                        found_correct_lemma_and_pos_and_morph = True
        
        if found_correct_lemma_and_pos_and_morph:
            results[transducername]['correct: lemma/pos + morph'] += 1
            results[transducername]['correct: lemma/pos'] += 1
            results_pos[transducername][word_info['pos']]['correct: lemma/pos + morph'] += 1
            results_pos[transducername][word_info['pos']]['correct: lemma/pos'] += 1
        elif found_correct_lemma_and_pos:
            results[transducername]['correct: lemma/pos'] += 1
            results_pos[transducername][word_info['pos']]['correct: lemma/pos'] += 1
        else:
            results[transducername]['fail: no correct analysis found'] += 1
            results_pos[transducername][word_info['pos']]['fail: no correct analysis found'] += 1
        results[transducername]['total'] += 1
        results_pos[transducername][word_info['pos']]['total'] += 1

#print("\n\nResults:\n")
#print(results)
#print("\n\nResults differentiated by pos:\n")
#print(results_pos)

datestring = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
dumpYaml(results, "results/" + datestring + "_eval_results" + ".yaml")
dumpYaml(results_pos, "results/" + datestring + "_eval_results_pos" + ".yaml")

