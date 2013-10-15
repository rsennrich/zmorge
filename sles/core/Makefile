default: all

# ==============================================================================
# configuration:
# ==============================================================================

TARGETS = inflected.a

SOURCES = $(TARGETS:.a=.fst)

inflected.a: phon.a

.PHONY: default all clean

# ==============================================================================
# build targets:
# ==============================================================================

all: Makefile $(TARGETS)

clean:
	rm -f *.a *.ca

Makefile: *.fst
	makedepend -Y -o.a *.fst 2>/dev/null

# ==============================================================================
# pattern rules:
# ==============================================================================

%.a: %.fst
	fst-compiler $< $@

%.ca: %.a
	fst-compact $< $@
	fst-compact -s $< $(@:.ca=.s.ca)

# DO NOT DELETE

inflected.a: alphabet.fst flexion.fst
