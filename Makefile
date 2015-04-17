SRCS = $(wildcard *.asm)

all: $(SRCS:%.asm=%.mif)

%.mif: %.asm
	./assembler.py $< > $@


TEST_SRCS = $(wildcard test/*.asm)

test_results/%.mif: test/%.asm #test/%.mif
	@mkdir -p $(dir $@)
	./assembler.py $< > $@
	if [ -e $(<:%.asm=%.mif) ] ; then diff -uw $(<:%.asm=%.mif) $@ ; fi

test: $(TEST_SRCS:test/%.asm=test_results/%.mif)


clean:
	rm -fr test_results $(SRCS:%.asm=%.mif)


.PHONY: test clean
