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

$Stem$   = [#LETTER#][#letter#]+
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
  % c) -st or -est                                      ==> <Adj+(e)>
  $stem$[^sßxz]        [<Adj+><Adj+(e)>] | \
  $stem$               [<Adj+e>] | \
  $stem$[ß]            [<Adj~+e>] | \
  $stem$e[lr]          [<Adj-el/er>] | \
  %
  % NOUNS
  % general naming convention: N{Gender}_{SgGen-suffix}_{PlNom-suffix}
  % (e)s/e
  $Stem$[^e]           [<NMasc_es_e><NNeut_es_e><NMasc_es_$e>] | \
  $Stem$[sß]           [<NMasc-s/sse><NNeut-s/sse><NMasc-s/$sse>] | \
  % (e)s/((i)e)n
  $Stem$[^e]           [<NMasc_es_en><NNeut_es_en>] | \
  $Stem$[^esßxz]       [<NMasc_s_en>] | \
  $Stem$(e|el|er)      [<NMasc_s_n><NNeut_s_n>] | \
  $Stem$([#cons#]&[^s])[<NNeut-0/ien>] | \
  % (e)s/er
  $Stem$[^e]           [<NMasc_es_$er><NNeut_es_$er>] | \
  $Stem$[sßxz]         [<NNeut_es_$er>] | \
  $Stem$[sß]           [<NNeut-s/$sser>] | \
  % s/s
  $Stem$[^sßxz]        [<NMasc_s_s><NNeut_s_s>] | \
  % s/-
  $Stem$[n]            [<NMasc_s_x><NNeut_s_x><NMasc_s_$x>] | \
  $Stem$(e|el|er)      [<NMasc_s_0><NNeut_s_0><NMasc_s_$>] | \
  % (e)n/(e)n
  $Stem$[^e]           [<NMasc_en_en>] | \
  $Stem$[e]            [<NMasc_n_n>] | \
  % -/e
  $Stem$[^e]           [<NFem_0_$e>] | \
  $Stem$[sß]           [<NFem-s/$sse>] | \
  $Stem$(nis)          [<NFem-s/sse>] | \
  % -/(e)n
  $Stem$[^e]           [<NFem_0_en>] | \
  $Stem$(e|el|er)      [<NFem_0_n>] | \
  $Stem$[sß]           [<NFem-s/ssen>] | \
  $Stem$(in)           [<NFem-in>] | \
  % -/s
  $Stem$[^sßxz]        [<NFem_0_s>]

% filter unwanted symbols that might have been introduced by the symbol class
% complement operator:
$RegLexWords$ =    ([#Letter#]|<ge>|<ge/zu>)* [#letter#] [#infl-class#] \
                || $RegLexWords$

% ensure that umlauting classes are applied to umlautable stems only:
#uml-class# = <Adj$><Adj$e><NFem-s/$sse><NFem_0_$><NFem_0_$e><NMasc-s/$sse>\
    <NMasc_es_$e><NMasc_es_$er><NMasc_n_n=$in><NMasc_s_$><NMasc_s_$x>\
    <NNeut-s/$sser><NNeut_es_$e><NNeut_es_$er><NNeut_s_$>
$RegLexWords$  = \
       ((.*                        ([#infl-class#] & [^#uml-class#])) |\
        (.* [auoAUO] ([au]? [#cons#]* (e[#cons#])?)?  [#uml-class#]) )\
    || $RegLexWords$

% there should be (at least) one vowel in a stem:
$RegLexWords$ = .*[#Vowel#].* || $RegLexWords$

% there should be (at least) one vowel before and after a <ge/zu> marker:
$RegLexWords$ =    ((.*[#Vowel#].* <ge/zu> .*[#Vowel#].*) | [^<ge/zu>]* ) \
                || $RegLexWords$

% there should be (at least) one vowel in a stem before a schwa-syllable:
#schwa-class# = <Adj-el/er><VVReg-el/er>\
                <NMasc_s_n><NNeut_s_n><NMasc_s_0><NNeut_s_0><NMasc_s_$>
$RegLexWords$ =    .*[#Vowel#].*e[lr]?[#schwa-class#] | [^#schwa-class#]* \
                || $RegLexWords$



% ==============================================================================
% Possible lexical words: sth + irregular inflectional stem
% ==============================================================================

% load lexicon:
$Lexicon$ = "lexicon/slex"

% extract lexical words that can function as a head:
$IrregLexHeads$ = <>:<Head> .* || $Lexicon$ || <Head>:<> .*

% irregular nouns:
% decapitalise first letter on both levels (not very efficient, though; it
% would be better to have only decapitalised letters in the lexicon; but I
% leave it as it is...):
$IrregNounHeads$ =    [#letter_#]:[#LETTER#] [#any#]* [#infl-nn#] \
                   || $IrregLexHeads$ \
                   || [#LETTER#]:[#letter_#] [#any#]* [#infl-nn#]
$IrregNouns$     = [#LETTER#][#letter#]+ $IrregNounHeads$

% irregular adjectives:
% [PENDING]
% Would that be useful given that the adjectival inflectional paradigm in
% SMOR includes the comparative and superlative??? It seems to me that
% compounds with an adjectival head are always restricted to the positive.

% Complex Irregular Verbs
% two general types:
% 1) prefixed irregular verbs
% 2) "particle verbs" (written in one word if in subordinate clauses)
% convention: the left boundary of the simplex irregular verb is always
% marked with an <x> to avoid spurious ambiguities such as "verbrannte"
% analysed as a form of "brennen" vs a form of "rennen"
% <ge/zu> may occur left of <x>

% Prefix Verbs
% prefixes are restricted to the following, cf. Duden-Grammatik (2005), §1049:
$Prefix$ = (be|ent|er|ge|miß|ver|zer|durch|unter|über|um|unter|wider)
$IrregVerbHeads-pref$ =    (<>:<ge>| [^<ge>]) <x>:<> [#letter#]* <VIrreg> \
                        || $IrregLexHeads$ \
                        || (<ge>:<>|[^<ge>]) [#any#]*
$IrregVerbs-pref$     = $Prefix$ $IrregVerbHeads-pref$

% Particle Verbs
% If the base forms its past participle with "ge-" then "-ge-" is also
% required for the particle verb:
$IrregVerbHeads-part$ =    (<ge/zu>:<ge> | [^<ge>]) <x>:<> [#letter#]* <VIrreg>\
                        || $IrregLexHeads$ \
                        || (<ge>:<ge/zu>|[^<ge>]) [#any#]*
$IrregVerbs-part$     = [#letter#][#letter#]+ $IrregVerbHeads-part$


% all irregular lexical words:
$IrregLexWords$ = $IrregNouns$ | $IrregVerbs-pref$ | $IrregVerbs-part$



% ==============================================================================
% Possible lexical words: regular lexical words + irregular lexical words
% ==============================================================================

$LexWords$ = $RegLexWords$ | $IrregLexWords$



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

% OLD ORTHOGRAPHY (cf. README and helper.fst:$Orth-Filter$)
% enforce old orthography:
$MorphSynWords$ = [^<NEWORTH>]* || $MorphSynWords$
% map the orthograhphy marker to zero:
$MorphSynWords$ = ([^#orth#] | <>:[#orth#])* || $MorphSynWords$
% Also ensure that no stem -- apart from verbal stems -- ends in "ss". This
% is because all stems but verbal stems are also word forms and are represented
% according to the old orthography in SMOR.
$not-ss$        = (!(ss) & [#letter#][#letter#])
$MorphSynWords$ = .* ($not-ss$[#infl-class#] | [#infl-v#]) .* || $MorphSynWords$

% differentiate between <SS> in old and new orthography (cf. helper.fst):
$MorphSynWords$ = $MorphSynWords$ || $Orth-Filter$

% apply morphophonological and orthographic rules:
$Phon$ = "<core/phon.a>"
$Morph$ = <>:<WB> $MorphSynWords$ <>:<WB> || $Phon$

% resolve disjunctive features, e.g. <NA> --> <Nom>|<Acc>
$Morph$ = $Resolve-Disjunctions$ || $Morph$

% final transducer:
$Morph$

