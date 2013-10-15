import re
import fileinput 
from collections import defaultdict
from datetime import datetime
import pexpect
import time
import yaml
import sys
import wiktionary_config as config

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    print "could not load the faster cloader/cdumper for yaml package.\n will load standard loader/dumper"
    from yaml import Loader, Dumper

class FstWrapper():
    def __init__(self):
        if config.debug_lvl > 0: print "try to execute following command:\n'" + config.exec_string + "'"
        self.child = pexpect.spawn(config.exec_string)
        self.child.delaybeforesend = 0
        self.child.expect(["analyze> ", pexpect.EOF])
        self.morAnalyseMode = config.morAnalyseMode 
        # regex for stem guessing NOTE: for now only used for adjectives
        self.regex_adj_stem = re.compile("^(.*?)<") # TODO: move to regex file
        if config.debug_lvl > 0: print self.child.before

    def analyse(self, word):
        word = word.strip()
        if word == "":
            return None
        # if not in analyse mode, go to it
        if self.morAnalyseMode == False: 
            # print "Was not in analyse mode => toggle to it!"
            self.toggleMorMode()
            self.child.sendline("") # "" is used in the fst-mor to toggle between analyse/generate
            self.child.expect(["analyze> ", pexpect.EOF])
            self.child.before
        self.child.sendline(word)
        self.child.expect(["analyze> ", pexpect.EOF])
        result = self.child.before.split("\r\n")[1:-1]
        if len(result) == 1 and re.match("^no result for ", result[0]):
            result = None
        return result

    def generate(self, word):
        word = word.strip()
        if word == "":
            return None
        # if not in analyse mode, go to it
        if self.morAnalyseMode == True: 
            # print "Was not in generate mode => toggle to it!"
            self.toggleMorMode()
            self.child.sendline("") # "" is used in the fst-mor to toggle between analyse/generate
            self.child.expect(["generate> ", pexpect.EOF])
            self.child.before
        self.child.sendline(word)
        self.child.expect(["generate> ", pexpect.EOF])
        result = self.child.before.split("\r\n")[1:-1]
        if len(result) == 1 and re.match("^no result for ", result[0]):
            result = None
        return result

    # if you just want to play around you can use this function
    def openShell(self):
        if config.debug_lvl > 0: print "try to execute following command:\n'" + config.exec_string + "'"
        self.child = pexpect.spawn(config.exec_string)
        # self.child.logfile = sys.stdout  # TODO: ... log file could be neat
        while True:
            if self.morAnalyseMode == True:
                if config.debug_lvl > 0: print "### in analyse mode"
                self.child.expect(["analyze> ", pexpect.EOF])
            else:
                if config.debug_lvl > 0: print "### in generate mode"
                self.child.expect(["generate> ", pexpect.EOF])
            if config.debug_lvl > 0: print "################################\n", self.child.before, "############################\n"
            input_string = raw_input("input<<<<")
            if config.debug_lvl > 0: print "Sending an input to the prog:", input_string
            if input_string == "":
                if config.debug_lvl > 0: print "input string was '\\nn' => toggle to Mode"
                self.toggleMorMode()
            self.child.sendline(input_string)

    def toggleMorMode(self):
        self.morAnalyseMode = not self.morAnalyseMode

    # this function will return the possible analysis
    # @analysis: must be a list of possible analysis
    # @filterStrings: a list of not regex strings
    def filterAnalysis(self, analysis, filterStrings, wordstem, pos):
        filteredAnalysis = []
        # compile all the regexes
        filterRegexes = []
        for filterString in filterStrings:
            filterRegexes.append(re.compile(".*" + re.escape(filterString)+ ".*" ))
        if analysis == None:
            return []
        for ana in analysis:
            possibleAna = True
            for filterRegex in filterRegexes:
                match = filterRegex.match(ana)
                if match == None:
                    possibleAna = False
                    break # breaks out of the inner loop (filterRegexes for loop)

            # NOTE: following are hardcoded special rules
            if pos == 'ADJ':
                try:
                    match = self.regex_adj_stem.match(ana).group(1)
                    if match == wordstem:
                        pass
                    else:
                        possibleAna = False
                        # print("Special filtering for Adjective: filtered => " + ana)
                except Exception as e:
                    print e
                    possibleAna = False

            if possibleAna == True: # if it is still true, then add it
                filteredAnalysis.append(ana)
        return filteredAnalysis

    # find all fst symbols described in 'symbols.fst' # TODO: add link/ref to page/file
    # @analysis: ONE analysis
    def findSymbols(self, analysis):
        symbols = []
        r = re.compile("<(.*?)>");
        for match in r.finditer(analysis):
            symbols.append(match.group(1))
        return symbols

    # this function returns the inflectional class of the given analysis
    # TODO: write many tests for this thing!
    # returns inflectional class or None
    # @analysis: ONE analysis
    def determineInflClass(self, analysis):
        # first find all symbols
        symbols = self.findSymbols(analysis)
        if len(symbols) == 0:
            if config.debug_lvl > 0: print "no inflectional class could be found (even no symbols)"
            return None # no symbols => no infl class 

        # look for inflectional class(es) symbol NOTE: only ONE inflectional class should be found
        # TODO: do regex compilation at the beginning of script/class

        # NOTE: these classes will not be regex-escaped! so be careful
        nouns = ["NMasc","NFem","NNeut","N\?","NTrunc"] 
        noms = ["NSMasc", "NSFem", "NSNeut", "^NS\-er$"] # TODO: NS... are 'nom-classes'. should they be added?
        names = ["^Name\-", "^FamName_"]
        numbers = ["^Card", "^DigOrd$", "^Ord$", "^NumAdjFlex$"]
        verbs = ["^VA","^VI", "^VM", "^VP", "^VV"]
        adjs = ["^Adj"]
        abks = ["^Abk_"] # abbriviations
        # the messy others # TODO ...
        others = [] 

        allInfclasses = nouns + names + numbers + verbs + adjs + abks + others # TODO: add 'noms' ?

        r = re.compile("|".join(allInfclasses)) # OR them all 

        inflClasses = []
        for sym in symbols:
            if r.match(sym) != None:
                inflClasses.append(sym)

        if len(inflClasses) > 1:
            print "SEVERAL INFLECTIONAL CLASSES FOUND! NOT POSSIBLE!" # TODO: error handling
            return None # TODO: or return None ?! or all?  inflClasses 

        if len(inflClasses) == 0:
            print "no inflectional class could be found"
            return None

        # when here, everything is ok
        return inflClasses[0]
