PYTHON ?= python3
PYTHON_FLAGS += -OO

ASSIGNMENT = 05
GROUP = gr1
PACKFILE = uebung$(ASSIGNMENT)-$(GROUP).tar.xz

rwildcard=$(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2) $(filter $(subst *,%,$2),$d))
MODULES = $(call rwildcard, src, *.py)

.PHONY: optimized unittests clean pack

optimized: $(MODULES)
	$(PYTHON) $(PYTHON_FLAGS) -m compileall $^

unittests:
	export PYTHONPATH=src; \
	find tests -name test\*.py | while read -r test; do \
		$(PYTHON) "$$test" || exit $$?; \
	done

clean:
	rm -rf $(addsuffix c, $(MODULES)) $(addsuffix o, $(MODULES)) $(call rwildcard, tests, *.pyc *.pyo)

$(PACKFILE): $(MODULES) $(call rwildcard, tests, test*.py) Makefile README | tests
	tar -caf $@ -- $^

pack: $(PACKFILE)
