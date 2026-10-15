.PHONY: test workflows check gate

workflows:  ## regenerate canonical/workflows/abacus-*.js from _body.js
	PYTHONPATH=lib python3 -m abacus_standards.genworkflows

test:
	PYTHONPATH=lib python3 -m unittest discover -s tests -t .

check: test
gate: test
