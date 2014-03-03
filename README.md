Zmorge - The Zurich Morphological Analyzer for German
=====================================================

This project contains scripts to extract a morphological lexicon for German from Wiktionary,
which can be used with the SMOR morphology to build a morphological analyzer.

Pre-compiled analyzers are available at http://kitt.ifi.uzh.ch/kitt/zmorge/

REQUIREMENTS
------------

This software requires the following packages:

    Python 2.6 or newer
    Pexpect 3.0 or newer
    SFST 1.4.6g or newer


INSTALLATION
------------

1. Install all requirements. In Ubuntu Linux, all are available in the repositories:
    `sudo apt-get install python-pexpect sfst`

2. unpack (or git clone) the directory to your target directory.

3. compile SLES
    `cd sles && make`


USAGE INSTRUCTIONS
------------------

1. get the newest Wiktionary dump from http://dumps.wikimedia.org/ , and extract it
   (choose the file dewiktionary-{date}-pages-articles-multistream.xml.bz2)

2. extract the lexicon:
    `python extract_from_wiki_dump.py dewiktionary-{date}-pages-articles-multistream.xml output_file.xml`

3. to build a morphological analyzer, follow the instructions at https://github.com/rsennrich/SMORLemma

LICENSE
-------

Zmorge is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License (see LICENSE).


PUBLICATIONS
------------

Rico Sennrich and Beat Kunz. 2014:
   Zmorge: A German Morphological Lexicon Extracted from Wiktionary.
   In Proceedings of the 9th International Conference on Language Resources and Evaluation (LREC 2014).
