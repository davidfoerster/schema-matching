PYTHON ?= python
PYTHON_FLAGS += -OO

ASSIGNMENT = 05
GROUP = gr1
PACKFILE = uebung$(ASSIGNMENT)-$(GROUP).tar.xz

MODULES = schema-matching.py $(wildcard collector/*.py) $(wildcard utilities/*.py)

.PHONY: optimized clean pack

optimized: $(MODULES)
	$(PYTHON) $(PYTHON_FLAGS) -m compileall $^

clean:
	rm -rf $(addsuffix c, $(MODULES)) $(addsuffix o, $(MODULES))

$(PACKFILE): $(MODULES) Makefile README
	tar -caf $@ -- $^

pack: $(PACKFILE)
