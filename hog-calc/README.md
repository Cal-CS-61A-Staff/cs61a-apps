# `hog-calc`

This contains methods used to compare strategies for Hog. 

## Running Locally

Create a venv and install dependencies.

```bash
$ python3 -m venv env
$ env/bin/pip install -r requirements.txt
```

Run `env/bin/python main.py` to start the Flask server, then make a POST request
to `http://localhost:5000/api/compare_strategies` to start comparing strategies.
