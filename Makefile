install:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt

play:
	./venv/bin/python worldmap.py
