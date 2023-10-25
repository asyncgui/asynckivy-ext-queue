test:
	python -m pytest ./tests

html:
	sphinx-build -b html ./sphinx ./docs

livehtml:
	sphinx-autobuild -b html ./sphinx ./docs
