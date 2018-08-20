install:
	virtualenv -ppython3 venv
	./venv/bin/pip install -r requirements.txt

play:
	./venv/bin/python main.py
