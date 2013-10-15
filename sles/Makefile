default: all

# ==============================================================================
# configuration:
# ==============================================================================

TARGETS = sles.a

SUBDIRS = core lexicon

sles.a: core/inflected.a

.PHONY: default all clean subdirs $(SUBDIRS)

# ==============================================================================
# build targets:
# ==============================================================================

all: Makefile subdirs $(SUBDIRS) $(TARGETS)

clean:
	rm -f *.a *.ca
	$(MAKE) -C core clean
	$(MAKE) -C lexicon clean

Makefile: *.fst
	makedepend -Y -o.a *.fst 2>/dev/null

subdirs: $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@

# ==============================================================================
# pattern rules:
# ==============================================================================

%.a: %.fst
	fst-compiler-utf8   $< $@
	fst-compact    $(@) $(@:.a=.ca)
	fst-compact -s $(@) $(@:.a=.s.ca)