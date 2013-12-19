from __future__ import unicode_literals, print_function
### generell confs
debug_lvl = 0
# if debug_lvl higher then 0 this path will be loaded in extractFromWikidump (if none given)
debug_wikidump = "/home/beet/00_studien_zeugs/wiktionary_morph_builder/data/test_file.xml" 
nondebug_wikidump = "/home/beet/00_studien_zeugs/wiktionary_morph_builder/data/dewiktionary-20130129-pages-articles.xml"

num_processes = 4
# pathToMorphistoXml = "/home/beet/sda8/00_cl_praktikum_data/morphisto_lexikon/lexicon.xml"
pathToMorphistoXml = "/home/beet/00_studien_zeugs/morphisto_lexicon/lexicon.xml"   # for my server

### fst_stuff
# base_dir = "/media/sda8/00_cl_praktikum_data/" 
base_dir = "/home/beet/00_studien_zeugs/wiktionary_morph_builder/tools/00_cl_praktikum_data/"

smor_fst_dir = base_dir + "smor/SMOR_big/SFST/"
# sles_bin = base_dir + "morphology_mining/share/fst/sles.a" # the old one
sles_bin = "sles/sles.a" # new one
fst_mor_bin = "fst-mor"
# fst_infl_bin = "fst-infl"
# fst_infl2_bin = "fst-infl2"
morAnalyseMode = True # fst-mor starts in analyse mode
exec_string = smor_fst_dir + "./" + fst_mor_bin + " " + sles_bin
