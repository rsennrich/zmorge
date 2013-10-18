%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% File:    sles.fst
% Author:  Peter Adolphs
% License: GNU Public License version 2
% Content: core transducer for lexical entry speculation
%          maps word forms to hypothetical lexical entries + their
%          morphosyntactic properties, and vice versa
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#include "core/alphabet.fst"
#include "core/helper.fst"



% ==============================================================================
% Possible lexical words: regular inflectional stem + inflectional class
% ==============================================================================

ALPHABET = [#Letter#] [#infl-class#] [#lexchar#]

$Stem$   = [#LETTER#][#Letter#]*
$stem$   = [#letter#]+
$stem-v$ = (<ge>? [#letter#]+) | ([#letter#][#letter#]+<ge/zu>[#letter#]+)

% general conventions of the SMOR inflectional classes:
% $:      umlaut
% ~:      if the stem ends in "s" or "ß"
% -s/sse: stem ends in "s" which is doubled if followed by "e"
$RegLexWords$  = \
  % VERBS
  % regular verbs, comprising the default case and the special case that
  % the stem ends in a schwa-syllable
  % "e" at the end of a regular verbs' stem is not allowed because even
  % if there would be a verb such as "brieen", phon.fst:$R3$ would eliminate
  % it (e-elision after e). So why allow it here then?? ...
  $stem-v$[^e]         [<VVReg>] | \
  $stem-v$e[lr]        [<VVReg-el/er>] | \
  %
  % ADJECTIVES
  % comparative without umlaut, superlative with
  % a) -st (not if the stem already ends in an s-sound) ==> <Adj+>, <Adj-el/er>
  % b) -est (obligatory if the stem ends in an s-sound) ==> <Adj+e>, <Adj~+e>
  % c) -st or -est                                      ==> <Adj+> and <Adj+e>
  $stem$[^sßxz]        [<Adj+><Adj$>] | \
  $stem$               [<Adj+e><Adj$e>] | \
  $stem$[ß]            [<Adj~+e>] | \
  $stem$e[lr]          [<Adj-el/er>] | \
  %
  % NOUNS
  % general naming convention: N{Gender}_{SgGen-suffix}_{PlNom-suffix}
  % (e)s/e
  $Stem$[^e]           [<NMasc_s_$e><NMasc_s_e><NMasc_es_e><NNeut_s_e><NNeut_es_e><NMasc_es_$e>] | \
  $Stem$[sß]           [<NMasc-s/sse><NNeut-s/sse><NMasc-s/$sse>] | \
  % (e)s/((i)e)n
  $Stem$[^e]           [<NMasc_es_en><NNeut_es_en>] | \
  $Stem$[^esßxz]       [<NMasc_s_en><NNeut_s_en>] | \
  $Stem$(e|el|er)      [<NMasc_s_n><NNeut_s_n>] | \
  $Stem$([#cons#]&[^s])[<NNeut-0/ien>] | \
  % (e)s/er
  $Stem$[^e]           [<NMasc_es_$er><NNeut_es_$er>] | \
  $Stem$[^e]           [<NMasc_es_er><NNeut_es_er>] | \
  $Stem$[sß]           [<NNeut-s/$sser>] | \
  % s/s
  $Stem$[^sßxz]        [<NMasc_s_s><NNeut_s_s><NFem_s_s>] | \
  % s/-
  $Stem$[n]            [<NMasc_s_x><NNeut_s_x><NMasc_s_$x>] | \
  $Stem$(e|el|er)      [<NMasc_s_0><NNeut_s_0><NMasc_s_$><NNeut_s_$>] | \
  % (e)n/(e)n
  $Stem$[^e]           [<NMasc_en_en>] | \
  $Stem$[re]           [<NMasc_n_n>] | \
  % -/e
  $Stem$[^e]           [<NFem_0_$e><NFem_0_e>] | \
  $Stem$(er|el)        [<NFem_0_$>] | \
  $Stem$[sß]           [<NFem-s/$sse>] | \
  $Stem$(nis)          [<NFem-s/sse>] | \
  % -/(e)n
  $Stem$[^e]           [<NFem_0_en>] | \
  $Stem$(e|el|er)      [<NFem_0_n>] | \
  $Stem$[sß]           [<NFem-s/ssen>] | \
  $Stem$(in)           [<NFem-in>] | \
  % -/s
  $Stem$[^sßxz]        [<NFem_0_s>] | \
  % -/-
  $Stem$               [<NFem_0_x><NMasc_0_x><NNeut_0_x>] | \
  % us/en; us/i
  $Stem$ us            [<NMasc-us/en><NMasc-us/i>] | \
  % um/a; um/en
  $Stem$ um            [<NNeut-um/a><NNeut-um/en>] | \
  % on/a;
  $Stem$ on            [<NNeut-on/a>] | \
  % a/ata; a/en
  $Stem$ a             [<NNeut-a/ata><NNeut-a/en><NFem-a/en>] | \
  % is/en; is/iden
  $Stem$ is             [<NFem-is/en><NFem-is/iden>] | \
  % ns
  $Stem$ e             [<NMasc-ns>]

% filter unwanted symbols that might have been introduced by the symbol class
% complement operator:
$RegLexWords$ =    ([#Letter#]|<ge>|<ge/zu>)* [#Letter#] [#infl-class#] \
                || $RegLexWords$

% ensure that umlauting classes are applied to umlautable stems only:
#uml-class# = <Adj$><Adj$e><NFem-s/$sse><NFem_0_$><NFem_0_$e><NMasc-s/$sse>\
    <NMasc_es_$e><NMasc_es_$er><NMasc_n_n=$in><NMasc_s_$><NMasc_s_$x>\
    <NNeut-s/$sser><NNeut_es_$e><NNeut_es_$er><NNeut_s_$>
$RegLexWords$  = \
       ((.*                        ([#infl-class#] & [^#uml-class#])) |\
        (.* [auoAUO] ([au]? [#cons#]* (e[#cons#])?)?  [#uml-class#]) )\
    || $RegLexWords$

% there should be (at least) one vowel before and after a <ge/zu> marker:
$RegLexWords$ =    ((.*[#Vowel#].* <ge/zu> .*[#Vowel#].*) | [^<ge/zu>]* ) \
                || $RegLexWords$

% there should be (at least) one vowel in a stem before a schwa-syllable:
#schwa-class# = <Adj-el/er><VVReg-el/er>\
                <NMasc_s_n><NNeut_s_n><NMasc_s_0><NNeut_s_0><NMasc_s_$>
$LexWords$ =    .*[#Vowel#].*e[lr]?[#schwa-class#] | [^#schwa-class#]* \
                || $RegLexWords$



% ==============================================================================
% Build morphosyntactic words
% ==============================================================================

% compose lexical words with the transducer for inflected words
$MorphSynWords$ = $LexWords$ [#infl-sym#]* || "<core/inflected.a>"

% introduce orthography marker (required since orthography should be consistent
% throughout the stem):
$MorphSynWords$ = $MorphSynWords$ [#orth#]?



% ==============================================================================
% Filter specific forms
% ==============================================================================

ALPHABET = [#Letter#] [#infl-class#] [#lexchar#] [#infl-prop#] [#orth#]

% throw away <Simp> and <Old> forms:
$MorphSynWords$ = [^#infl-misc#]* || $MorphSynWords$



% ==============================================================================
% Spell-out
% ==============================================================================

ALPHABET = [#Letter#] [#infl-class#] [#lexchar#] [#infl-prop#] [#orth#]

% map the orthograhphy marker to zero:
$MorphSynWords$ = ([^#orth#] | <>:[#orth#])* || $MorphSynWords$

% differentiate between <SS> in old and new orthography (cf. helper.fst):
$MorphSynWords$ = $MorphSynWords$ || $Orth-Filter$

% apply morphophonological and orthographic rules:
$Phon$ = "<core/phon.a>"
$Morph$ = <>:<WB> $MorphSynWords$ <>:<WB> || $Phon$

% resolve disjunctive features, e.g. <NA> --> <Nom>|<Acc>
$Morph$ = $Resolve-Disjunctions$ || $Morph$

% final transducer:
$Morph$

