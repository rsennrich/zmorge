%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% File:    helper.fst
% Author:  Peter Adolphs
% License: GNU Public License version 2
% Content: various helper transducers that are needed by SLES and SLEX
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


% fetch lexical entry:
$Fetch-Lexentry$    = [#char# #lexchar#]* [#infl-class#]? \
                      (<>:[#infl-prop#])* [#orth#]? 

% fetch lemma + morphosyntactic properties:
% generate "-(e)n" for verbs (this does not work properly for "sein" and "tun")
$Fetch-Lemma+Props$ =    ([#char#] | <>:[#lexchar#] | <>:[#infl-class#])* \
                         [#infl-prop#]* [#orth#]? \
                      || (.* e:<> n:<> ([#infl-v#] & [^<VVReg-el/er>]) .* | \
                          .*      n:<> ([<VVReg-el/er>])               .* | \
                          [^#infl-v#]*                                    )

% fetch lemma:
$Fetch-Lemma$       = ([^#infl-sym#] | <>:[#infl-sym#])* || $Fetch-Lemma+Props$

% resolve disjunctive features, e.g. <NA> --> <Nom>|<Acc>
$Resolve-Disjunctions$ = ([^#disjunctive-features#] | \
                          [<1><3>]:<13> | \
                          [<Dat><Acc>]:<DA> | \
                          [<Gen><Acc>]:<GA> | \
                          [<Gen><Dat>]:<GD> | \
                          [<Gen><Dat><Acc>]:<GDA> | \
                          [<Nom><Acc>]:<NA> | \
                          [<Nom><Dat><Acc>]:<NDA> | \
                          [<Nom><Gen><Acc>]:<NGA> | \
                          [<Nom><Gen><Dat><Acc>]:<NGDA> | \
                          [<Pred><Adv>]:<PA> | \
                          [<Masc><Neut>]:<MN>)*

% Replace <SS> with one of the three possibilities. Also set a marker for
% old or new orthography if a word form does differ in this respect, and
% ensure that old and new orthography are not mixed (cf. README):
$Orth-Filter$ = ([^<SSalt><SSneu> #orth#]*                         | \
                 [^<SSalt>]* <SS>:<SSneu> [^<SSalt>]* <NEWORTH>:<> | \
                 [^<SSneu>]* <SS>:<SSalt> [^<SSneu>]* <OLDORTH>:<>   )

