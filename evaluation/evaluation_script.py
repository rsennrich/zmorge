#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright ©2013 University of Zürich
# Author: Beat Kunz <beat.kunz@access.uzh.ch>

from __future__ import unicode_literals, print_function, division
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
    print("could not load the faster cloader/cdumper/csafedumper for yaml package.\n will load standard loader/dumper")
    from yaml import Loader, Dumper, SafeDumper

##### set files
# benchmark_file_name = 'r7-test.conll'
benchmark_file_name = 'r7-dev.conll'
shell_script_name = './create_test_output.sh'
analysis_dir = 'testoutput'

##### call bash scripts that generate analysis of 
print(('Python calls shell script', shell_script_name, 'with', benchmark_file_name))
call([shell_script_name, benchmark_file_name])
# print('Python finished calling the shell script')

re_mainclass = re.compile('<\+(.*?)>')
re_any = re.compile('<(.*?)>')
re_segment = re.compile('<([A-Z\^]*?)>')
re_last = re.compile('(?:^|\W)([\w\.]+?)(?:<[\w\-\^~#]*>)*?<\+',re.UNICODE)
re_hyphenation = re.compile('{(.+?)}-')

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
        if line.startswith('haben') or line.startswith('werden') or line.startswith('sein') or line.startswith('hab<~>en') or line.startswith('werd<~>en') or line.startswith('sein'):
            pos += 'A'
        elif line.startswith('dürfen') or line.startswith('können') or line.startswith('sollen') or line.startswith('müssen') or line.startswith('mögen') or line.startswith('wollen') or line.startswith('dürf<~>en') or line.startswith('könn<~>en') or line.startswith('soll<~>en') or line.startswith('müss<~>en') or line.startswith('mög<~>en') or line.startswith('woll<~>en'):
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
            lemma = re_any.sub('',line)
            return re_hyphenation.sub(r'\1-',lemma)

        last_morpheme = last_morpheme.group(1)
        word_lc = word.lower()
        last_morpheme_lc = last_morpheme.lower()
        try:
            joinpoint = backTrack(LCS(word_lc,last_morpheme_lc),word_lc,last_morpheme_lc,len(word_lc),len(last_morpheme_lc))[0]
        except IndexError:
            lemma = re_any.sub('',line)
            lemma = re_hyphenation.sub(r'\1-',lemma)
            try:
                return lemma[0] + lemma[1:].lower()
            except IndexError:
                return lemma
        if joinpoint > 1:
            if word[joinpoint-1] == '-':
                lemma = re_any.sub('',word[:joinpoint])+last_morpheme
                return re_hyphenation.sub(r'\1-',lemma)
            else:
                lemma = re_any.sub('',word[:joinpoint])+last_morpheme_lc
                return re_hyphenation.sub(r'\1-',lemma)
        else:
            return last_morpheme
    
    lemma = re_any.sub('',line) #delete all markup, leaving what we'll use as lemma
    lemma = re_hyphenation.sub(r'\1-',lemma)


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

    return lemma

    #try:
        #return lemma[0] + lemma[1:].lower()
    #except IndexError:
        #return lemma

#### END functions


if __name__ == '__main__':

    ##### load benchmark ( / Gold-Daten ) and map grammatical analysis tags
    # load
    benchmark_file = open(benchmark_file_name)

    benchmark_dict = defaultdict(list)

    pos_v = [
                'VAFIN', 'VAINF', 'VAPP', 'VMINF','VMFIN', 'VVINF','VVFIN', 'VVPP', 'VVIMP','VVIZU'
            ]
#    pos_n = [
#                'NN', 'NE', 'NPROP'
#            ]

    pos_ne = ['NE', 'NPROP']
    pos_nn = ['NN']

    pos_adj = [ 
                'ADJA', 'ADJD'
            ]

    # NOTE: only these will be evaluated
    pos_all = pos_v + pos_ne + pos_adj + pos_nn

    pos_map = dict([(item,'V') for item in pos_v] + [(item,'NE') for item in pos_ne] + [(item,'NN') for item in pos_nn] + [(item,'ADJ') for item in pos_adj])

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
        if '#' in word_lemma and not '#' in word:
            try:
                prefix, stem = word_lemma.split('#')
                if word.startswith(prefix) or word.lower().startswith(prefix):
                    word_lemma = word_lemma.replace('#','')
                else:
                    word_lemma = stem
            except ValueError:
                pass
        if '%' in word_lemma and not '%' in word:
            word_lemma = word_lemma.split('%')[0]
        word_pos = splitted_line[4]
        if word_pos in pos_all:
            pass
        else:
            continue
        word_morph = splitted_line[5]
        # TODO: map morphological infos
        mapped_word_morph = {}
        word_morph += "******" # NOTE: cheap solution, so that there are always enough symbols
        # morph info for adjectives and nouns
        if word_pos in pos_nn or word_pos in pos_ne or word_pos in pos_adj:
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
        elif word_pos in pos_v:
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

        word_data = {'wordform': word, 'lemma': word_lemma, 'pos': word_pos, 'morph': mapped_word_morph}
        benchmark_dict[word].append(word_data)

    ## END of function imported from morphisto2prolog script


    ##### load different analysis into dict (dictionary build like this: diff_analysis['<analysis_type>']['<word>'] = [[<word1analysis1>, <word1analysis2>, ...], [<word2analysis1>, <word2analysis2>, ...] ])
    ##### for token stats
    diff_analysis = {}
    ##### load different analysis into dict (dictionary build like this: diff_analysis_type['<analysis_type>']['<word>'] = [<word1analysis1>, <word1analysis2>, ...]
    ##### for type stats
    diff_analysis_type = {}


    limit = 100
    for filename in os.listdir(analysis_dir):
        nr = 0
        #print("loading testouput: " + filename)
        diff_analysis[filename] = defaultdict(list)
        diff_analysis_type[filename] = defaultdict(lambda: None)
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
                    if not diff_analysis_type[filename][word]:
                        diff_analysis_type[filename][word] = word_analysis
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
            if pos in pos_all:
                ana = {'pos': pos, 'morph': extracted_morph, 'lemma': lemma}
                # print("Morph extracted:", ana['morph'])
                word_analysis.append(ana)

            if pos2 and pos2 in pos_all:
                ana = {'pos': pos2, 'morph': extracted_morph, 'lemma': lemma}
                # print("Morph extracted:", ana['morph'])
                word_analysis.append(ana)
        testoutput_file.close()
        # print("Finished loading:", diff_analysis[filename])
        # print("let's print the loaded analysis of " + filename )

    ## for token stats
    results = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    total = defaultdict(lambda: defaultdict(int))
    reported = defaultdict(set)

    for benchmark_word, word_info_all in list(benchmark_dict.items()):
        for word_info in word_info_all:
            typeinfo = (word_info['lemma'], word_info['pos'], tuple(sorted(word_info['morph'].items())))
            coarse_pos = pos_map[word_info['pos']]
            total[coarse_pos][typeinfo] += 1
            for transducername, twords in list(diff_analysis.items()):
                try:
                    word_info_anas = twords[benchmark_word]
                except:
                    continue # next transducer's proposals for this benchmark word
                found_correct_lemma_and_pos = False
                found_correct_lemma_and_pos_and_morph = False
                # print("Word_info_anas", word_info_anas)
                all_morph_correct = False
                for ana_list in word_info_anas:
                    for ana in ana_list:
                        #print("Ana:", ana)
                        #print("Benchmark:", word_info)
                        ##print('pos ana vs info: ' + word_info['pos'] + ' ' + ana['pos'])
                        if (word_info['lemma'].lower() == ana['lemma'].lower() or ('|' in word_info['lemma'] and ana['lemma'] in word_info['lemma'].split('|'))) and (word_info['pos'] == ana['pos'] or word_info['pos'] == 'NE' and ana['pos'] == 'NPROP'):
                            all_morph_correct = True  # NOTE: this stays only true if all morphological information given by the benchmark word can be found in the analysis
                            for morph_name, morph_value in list(ana['morph'].items()):
                                if morph_name in word_info['morph'] and morph_value != word_info['morph'][morph_name]:
                                    all_morph_correct = False
                                    break # from inner loop
                        if all_morph_correct:
                            break

                if all_morph_correct:
                    results[transducername][coarse_pos][typeinfo] += 1

#                else:
#                    if transducername == 'testoutput_smor-wiktionary21_boundaries.ca.txt' and coarse_pos == 'N':
#                        if not (word_info['wordform'], typeinfo) in reported[transducername]:
#                            print word_info['wordform'], typeinfo
#                            print word_info_anas
#                            reported[transducername].add((word_info['wordform'], typeinfo))

    #token stats: sum the number of occurrences of (correct) word forms
    print("token stats: name, NN, NE, V, ADJ, total")
    for transducername in results:
        recall_dict = defaultdict(float)
        for tag in ['NN', 'NE', 'V', 'ADJ']:
            recall = sum(results[transducername][tag].values()) / sum(total[tag].values())
            recall_dict[tag] = recall
        recall = sum(sum(results[transducername][tag].values()) for tag in results[transducername]) / sum(sum(total[tag].values()) for tag in total)
        recall_dict['total'] = recall
        print("{0:<15} & {1:.1f} & {2:.1f} & {3:.1f} & {4:.1f} & {5:.1f} \\\\".format(transducername, recall_dict['NN']*100, recall_dict['NE']*100, recall_dict['V']*100, recall_dict['ADJ']*100, recall_dict['total']*100))

    print('')

    #type stats: number of (correct) types corresponds to the length of the dictionaries
    print("type stats: name, NN, NE, V, ADJ, total")
    for transducername in results:
        recall_dict = defaultdict(float)
        for tag in ['NN', 'NE', 'V', 'ADJ']:
            recall = len(results[transducername][tag]) / len(total[tag])
            recall_dict[tag] = recall
        recall = sum(len(results[transducername][tag]) for tag in results[transducername]) / sum(len(total[tag]) for tag in total)
        recall_dict['total'] = recall
        print("{0:<15} & {1:.1f} & {2:.1f} & {3:.1f} & {4:.1f} & {5:.1f} \\\\".format(transducername, recall_dict['NN']*100, recall_dict['NE']*100, recall_dict['V']*100, recall_dict['ADJ']*100, recall_dict['total']*100))
