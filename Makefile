PYTHON ?= python3
PYTHON_FLAGS += -OO

ASSIGNMENT = 05
GROUP = gr1
PACKFILE = uebung$(ASSIGNMENT)-$(GROUP).tar.xz

rwildcard=$(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2) $(filter $(subst *,%,$2),$d))
MODULES = $(call rwildcard, , *.py)

.PHONY: optimized clean pack

optimized: $(MODULES)
	$(PYTHON) $(PYTHON_FLAGS) -m compileall $^

clean:
	rm -rf $(addsuffix c, $(MODULES)) $(addsuffix o, $(MODULES))

$(PACKFILE): $(MODULES) Makefile README
	tar -caf $@ -- $^

pack: $(PACKFILE)
