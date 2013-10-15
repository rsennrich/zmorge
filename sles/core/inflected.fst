%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% File:    inflected.fst
% Author:  Peter Adolphs
% License: GNU Public License version 2
% Content: transducer representing abstract morphosyntactic words
% 
% Description:
% This transducer maps lexical entries + inflectional properties to an
% abstract surface form. The surface form still has to undergo
% morphophonlogical processes to yield the final surface form.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#include "alphabet.fst"
#include "flexion.fst"



% ==============================================================================
% Possible lexical words (inflectional stem + inflectional class)
% ==============================================================================

ALPHABET   = [#Letter# #lexchar# #infl-class# #orth#] <e>

$Stem$     = [#Letter# #lexchar#] [#letter# #lexchar#]* 

% possible lexical words (inflectional stem + inflectional class):
$LexWords$ = $Stem$ [#infl-class#]

% for phon.fst
$LexWords$ = $LexWords$ || (.* e:<e> [lr] <VVReg-el/er> | [^<VVReg-el/er>]*)

% for phon.fst
% Replace "ss" at all verb stem ends with the special trigger "ß<SS>"
% (see also: $Orth-Filter$ in helper.fst):
$not-ss$     = !(ss) & [<e> #letter#][#letter#]
$Replace-ss$ = (.* (($not-ss$ | s:ß s:<SS>) [#infl-v#])) | [^#infl-v#]*
$LexWords$   = $LexWords$ || $Replace-ss$



% ==============================================================================
% Build Inflectional Patterns:
% ==============================================================================

ALPHABET   = [#Letter# #lexchar# #infl-class# #infl-prop# #orth#] <e>

$Inflected$ = $LexWords$ $FLEXION$ || $FLEXFILTER$



% ==============================================================================
% Verbal morphology between syntax and morphosyntax
% cf. $GE$, $ZU$, and $IMP$ in deko.fst
% ==============================================================================

ALPHABET = [#any#]

% The handling of "-zu-" and "(-)ge-" is a bit different to SMOR:
% - <ge> is only used for non-particle verbs that form their past participle
%   with "ge-".
% - SLES has a combined marker <ge/zu> that marks the position of "-ge-" and
%   "-zu-" in particle verbs
% As in SMOR, past participles are marked with <^pp> and infinitives with
% embedded "zu" with <^zz> by flexion.fst.

% Filter imperatives for particle verbs (that are written as one orthographic
% word). 3 cases:
% 1) pass anything that is no imperative and is no particle verb
% 2) pass a particle verb only if it is no imperative
% 3) pass an imperative only if it is no particle verb; delete the imperative
%    marker
$IMP$   =   [^<ge/zu><^imp>]* \
          | .* <ge/zu> [^<^imp>]* \
          | [^<ge/zu>]* <^imp>:<> .*

% Handle (-)ge- and -zu-. 3 cases:
% 1) pass anything that is not a past participle or infinitive with embedded
%    "-zu-"; in this case: delete <ge> and <ge/zu> if they occur
% 2) pass any past participle without a <ge> or <ge/zu> marker
% 3) <ge> and <ge/zu> are replaced by "ge" if it is a past participle;
%    delete the past participle marker
% 4) <ge/zu> is replaced by "zu" iff it is an infinitive with embedded "zu"
%    (lexical entries without <ge/zu> but with the marker for an infinitive
%     with embedded "zu" will be filtered out here)
$GE/ZU$ =   ([^<^pp><^zz>] | [<ge><ge/zu>]:<>)*    \
          | [^<ge><ge/zu>]*            <^pp>:<> .* \
          | .* {[<ge><ge/zu>]}:{ge} .* <^pp>:<> .* \
          | .* {<ge/zu>}:{zu}       .* <^zz>:<> .*

$Inflected$ = $Inflected$ || $IMP$ || $GE/ZU$




% ==============================================================================
% Upper / lower case markers
% cf. $UPLOW$ from deko.fst
% ==============================================================================

ALPHABET = [#any#]

$C$     = [#char# #lexchar# #infl-prop# #boundary# #trigger# #orth#] & [^<^UC><CB>]
$S$     = $C$ ($C$ | <CB>)*
$UpLow$ = <CB>:<>        $S$ <Fix#>:<> |\
          [<CB><>]:<^UC> $S$  <Up#>:<> |\
          [<CB><>]:<CB>  $S$ <Low#>:<>

$Inflected$ = $Inflected$ || $UpLow$



% ==============================================================================
% Final transducer
% ==============================================================================

$Inflected$

