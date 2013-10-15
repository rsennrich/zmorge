%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% File:    alphabet.fst
% Author:  Peter Adolphs
% License: GNU Public License version 2
% Content: named symbol classes for SMOR and SLES
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% =========================================================================
% Symbol Classes for SLES
% =========================================================================

% -------------------------------------------------------------------------
% Normal Graphemes
% -------------------------------------------------------------------------

#LETTER#       = A-ZÄÜÖ
#letter#       = a-zäüößé
#letter_#      = a-zäüö
#Letter#       = #LETTER# #letter#
#cons#         = bcdfghjklmnpqrstvwxyzß
#CONS#         = BCDFGHJKLMNPQRSTVWXYZ
#Cons#         = #cons# #CONS#
#vowel#        = aeiouyäöüé
#VOWEL#        = AEIOUYÄÖÜ
#Vowel#        = #vowel# #VOWEL#
#number#       = 0-9
#alphnum#      = #Letter# #number#
#punctuation#  = \-'
#char#         = #alphnum# #punctuation#

#lexchar#      = <ge><ge/zu><SS><Head><x>



% -------------------------------------------------------------------------
% External Tags wrt Inflection / Morphosyntax
% -------------------------------------------------------------------------

#infl-abbr# = \
  <Abk_ADJ><Abk_ADV><Abk_ART><Abk_DPRO><Abk_KONJ> \
  <Abk_NE-Low><Abk_NE><Abk_NN-Low><Abk_NN>\
  <Abk_PREP><Abk_VPPAST><Abk_VPPRES>

#infl-adj# = \
  <Adj$><Adj$e><Adj+(e)><Adj+><Adj&><Adj+Lang><Adj+e><Adj-el/er>\
  <Adj0><Adj0-Up><AdjComp><AdjSup><AdjFlexSuff>\
  <AdjNN><AdjNNSuff>\
  <AdjPos><AdjPosAttr><AdjPosAttr-Up><AdjPosPred><AdjPosSup><Adj~+e>

#infl-nn# = \
  <N?/Pl_0><N?/Pl_x>\
  <NFem-a/en><NFem-in><NFem-is/en><NFem-is/iden><NFem-s/$sse>\
  <NFem-s/sse><NFem-s/ssen><NFem/Pl><NFem/Sg><NFem_0_$><NFem_0_$e><NFem_0_e>\
  <NFem_0_en><NFem_0_n><NFem_0_s><NFem_0_x><NFem_s_s>\
  <NMasc-Adj><NMasc-ns><NMasc-s/$sse><NMasc-s/Sg><NMasc-s/sse><NMasc-s0/sse>\
  <NMasc-us/en><NMasc-us/i><NMasc/Pl><NMasc/Sg_0><NMasc/Sg_es><NMasc/Sg_s>\
  <NMasc_0_x><NMasc_en_en=in><NMasc_en_en><NMasc_es_$e><NMasc_es_$er>\
  <NMasc_es_e><NMasc_es_en><NMasc_es_er><NMasc_n_n=$in><NMasc_n_n=in><NMasc_n_n><NMasc_s_$>\
  <NMasc_s_$x><NMasc_s_0=in><NMasc_s_0><NMasc_s_e=in><NMasc_s_e><NMasc_s_en=in>\
  <NMasc_s_en><NMasc_s_n><NMasc_s_s><NMasc_s_x>\
  <NNeut-0/ien><NNeut-Herz><NNeut-Inner><NNeut-a/ata><NNeut-a/en>\
  <NNeut-on/a><NNeut-s/$sser><NNeut-s/sse><NNeut-um/a><NNeut-um/en><NNeut/Pl>\
  <NNeut/Sg_0><NNeut/Sg_es><NNeut/Sg_en><NNeut/Sg_s><NNeut_0_x><NNeut_es_$e>\
  <NNeut_es_$er><NNeut_es_e><NNeut_es_en><NNeut_es_er><NNeut_s_$><NNeut_s_0>\
  <NNeut_s_e><NNeut_s_en><NNeut_s_n><NNeut_s_s><NNeut_s_x>

#infl-nprop# = \
  <FamName_0><FamName_s><Name+er/in><Name-Fem_0><Name-Fem_s><Name-Invar>\
  <Name-Masc_0><Name-Masc_s><Name-Neut+Loc><Name-Neut_0><Name-Neut_s>\
  <Name-Pl_0><Name-Pl_x>

% <VIrreg> is special to SLES. it only occurs on the lexical tape of the
% lexicon
#infl-v# = \
  <VIrreg> \
  <VAImpPl><VAImpSg><VAPastKonj2><VAPres1/3PlInd><VAPres1SgInd>\
  <VAPres2PlInd><VAPres2SgInd><VAPres3SgInd><VAPresKonjPl><VAPresKonjSg>\
  <VInf><VInf+PPres><VMPast><VMPastKonj><VMPresPl><VMPresSg><VPPast>\
  <VPPres><VPastIndReg><VPastIndStr><VPastKonjStr><VPresKonj><VPresPlInd>\
  <VVPP-en><VVPP-t><VVPastIndReg><VVPastIndStr><VVPastKonjReg>\
  <VVPastKonjStr><VVPastStr><VVPres><VVPres1><VVPres1+Imp><VVPres2>\
  <VVPres2+Imp><VVPres2+Imp0><VVPres2t><VVPresPl><VVPresSg><VVReg><VVReg-el/er>

#infl-closed# = \
  <Circp>\
  <Intj><IntjUp>\
  <Konj-Inf><Konj-Kon><Konj-Sub><Konj-Vgl>\
  <Postp-Akk><Postp-Dat><Postp-Gen>\
  <Prep-Akk><Prep-Dat><Prep-Gen><Prep-DA><Prep-GD><Prep-GDA>\
  <Prep/Art-m><Prep/Art-n><Prep/Art-r><Prep/Art-s>\
  <ProAdv>\
  <Ptkl-Adj><Ptkl-Ant><Ptkl-Neg><Ptkl-Zu>\
  <WAdv>

% inflectional classes:
#infl-class# = \
  #infl-abbr# #infl-adj# #infl-nn# #infl-nprop# #infl-v# #infl-closed# \
  <Adv>\
  <Card><Card1><Ord><DigOrd>\
  <Trunc><NTrunc>\
  <NumAdjFlex>\
  <PInd-Invar>\
  <Pref/Adj><Pref/Adv><Pref/N><Pref/ProAdv><Pref/Sep><Pref/V>

% morpho-syntactic properties:
#pos# = <+ADJ><+ADV><+ART><+CARD><+CHAR><+CIRCP><+CONJ><+DEM><+INDEF><+INTJ> \
        <+NN><+NPROP><+ORD><+POSS><+POSTP><+PPRO><+PREP><+PREPART><+PROADV> \
        <+PTCL><+PUNCT><+REL><+SYMBOL><+TRUNC><+V><+VPART><+WADV><+WPRO>
#case# = <Nom><Gen><Dat><Acc>
#gender# = <Masc><Fem><Neut><NoGend>
#degree# = <Pos><Comp><Sup>
#mode# = <Inf><Ind><Subj><Imp>
#tense# = <Pres><Past><PPast><PPres>
#person# = <1><2><3>
#number# = <Sg><Pl>
#infl-class-type# = <St><Wk>
#conjunction-type# = <Inf><Coord><Sub><Compar>
#particle-type# = <Adj><Ans><Neg><Adv><ProAdv><NN><V><zu>
#adjective-type# = <Pred><Adv>
#art+noun-type# = <Attr><Subst><Pro>
#art+pronoun-type# = <Def><Indef><Pers><Prfl><Rec><Refl><WeakGen>
#disjunctive-features# = <13><DA><GA><GD><GDA><NA><NDA><NGA><NGDA><PA><MN>
#infl-misc#  = <Old><Invar><Simp>
#orth#       = <OLDORTH><NEWORTH>
#src-cat#    = <^ABBR><^ADJ><^VINF><^VPAST><^VPRES>
#punctuation-type# = <Left><Right><Norm><Comma>
#infl-prop# = #pos# #case# #gender# #degree# #mode# #tense# #person# #number# \
              #infl-class-type# #conjunction-type# \
              #particle-type# #adjective-type# #art+noun-type# \
              #art+pronoun-type# \
              #disjunctive-features#

#infl-sym# = #infl-class# #infl-prop# #infl-misc# #orth#



% -------------------------------------------------------------------------
% Internal Tags wrt Morphophonology
% -------------------------------------------------------------------------

% morpho-phono-graphemic triggers:
% <e>      schwa
% <ge>     marks in SMOR where "ge" should be inserted
% <zu>     double function!! (cf. #particle-type#); marks in SMOR where "zu"
%          should be inserted in complex particle verb stems from the lexicon
%          (cf. map.fst and $ZU$ in deko.fst)
% <SS>     will be replaced with "ss" if followed by a vowel (cf. README)
% <SSalt>  will be replaced with "?"  if followed by a consonant in old orth.
% <SSneu>  will be replaced with "ss" if followed by a consonant in new orth.
% <UL>     umlaut (for nouns and adjectives; replaces <FB>)
% <DEL-S>  e-epenthesis (replaces <FB>); e.g.: regn<DEL-S>t ==> regnet
%          (it is totally unclear to me why it is called DEL-S; it does not
%          seem to be about s-merging between stem and suffix)
% <^Ax>    e-elision in adjectives; e.g. dunkel<^Ax>e ==> dunkle
% <^Del>   e-elision in feminine nouns ending in e; e.g. Bote<^Del>in ==> Botin
% <^Gen>   e-elision in Gen Sg; e.g. Tisch<^Gen>es ==> Tischs, Tisches
% <^imp>   signals imperative; particle verbs with <^imp> are filtered out
% <^pl>    deletes inflectional suffix if set; e.g. Algebra<^pl>en ==> Algebren
% <^pp>    past participle, triggers "-ge-" insertion
% <^zz>    embedded "zu" infinitive, triggers "-zu-" insertion
% <^UC>    enforces upper case for the first character
#trigger#  = <e><ge><zu>\
             <SS><SSalt><SSneu>\
             <UL><DEL-S>\
             <^Ax><^Del><^Gen><^imp><^pl><^pp><^zz><^UC>

% boundaries:
% WB       word boundary
% CB       morpheme boundary (used to delimit morphemes in stems only)
% FB       inflection boundary
% triggers that may replace <FB>: <UL>, <DEL-S>
#boundary# = <WB><CB><FB><UL><DEL-S>

% inflection end markers with uppercase/lowercase indicator:
#closer#   = <Low#><Up#><Fix#>

#phon-sym# = #trigger# #boundary# #closer#



% -------------------------------------------------------------------------
% General Classes
% -------------------------------------------------------------------------

#meta#      = #infl-sym# #phon-sym#

#any#       = #char# #lexchar# #meta#

ALPHABET    = [#any#]




% =========================================================================
% Symbol Classes for SMOR Word Formation (not needed in SLES)
% =========================================================================

% type of the lexical entry:
#entry_type# = <Base_Stems><Deriv_Stems><Kompos_Stems><Pref_Stems><Suff_Stems>

% stem type feature (inflectional, derivational or compositional):
#stem_type#  = <base><deriv><kompos>

% origin feature (only relevant for word-formation)
#origin#     = <nativ><fremd><klassisch>

% stem sub-type for neo-classical items
#stem_subtype# = <kurz><lang>

% morphological status (only relevant for word-formation)
#status#     = <frei><gebunden>

% selection for complexity
#complexity# = <simplex><prefderiv><suffderiv><komposit>

% word-formation category
#wf_cat#     = <ABBR><ADJ><ADV><CAP><CARD><DIGCARD><NN><NPROP> \
               <ORD><PRO><V><VPART><VPREF><OTHER>

% prefix/suffix markers:
#pref_suff#  = <PREF><SUFF><QUANT>

% initial to the stem/morpheme definition:
#initial#    = <Initial><NoHy><NoDef><NoPref><no-ge>

% phonemes   in the lexicon for complex stems:
% <d>        for neoclassical prefixes; e.g. a<d>figieren ==> affigieren
% <n>        for neoclassical prefixes; e.g. i<n>loyal ==> illoyal
% <~n>       for neoclassical prefixes; e.g. a<~n>normal vs a<~n>organisch
#phoneme#    = <d><n><~n>

#misc#       = <Ge-Nom><X><F><UC><LC><CAP><DECAP>

#smor_disj#  = <frei,fremd,gebunden,kurz><frei,fremd,gebunden,lang> \
    <frei,fremd,gebunden,nativ><frei,fremd,gebunden><frei,fremd,kurz> \
    <frei,fremd,lang><frei,fremd,nativ><frei,fremd><frei,gebunden,kurz,lang> \
    <frei,gebunden,kurz><frei,gebunden,lang><frei,gebunden,nativ> \
    <frei,gebunden><frei,lang><frei,nativ><frei><fremd,gebunden,lang> \
    <fremd,klassisch,nativ><fremd,klassisch><fremd,nativ> \
    <gebunden,nativ><klassisch,nativ><klassisch> \
    <komposit,prefderiv,simplex,suffderiv><komposit,prefderiv,simplex> \
    <komposit,simplex,suffderiv><komposit,simplex> \
    <prefderiv,simplex,suffderiv><prefderiv,simplex><prefderiv,suffderiv> \
    <simplex,suffderiv>

#smor#       = #any# #entry_type# #stem_type# #origin# #stem_subtype# #status# \
               #complexity# #wf_cat# #pref_suff# #initial# #phoneme# \
               #misc# #smor_disj#


