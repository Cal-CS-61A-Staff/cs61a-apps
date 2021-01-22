# 61A Editor

Try the production version at https://code.cs61a.org!

## Web Editor

In the releases, download the latest `web.zip` file, activate the pipenv, and run `app.py` to start a Flask server. Alternatively, run

```
yarn
yarn web-dist
yarn web-dev
```

to start the editor in development mode. (You will need to add the additional files and run the setup for this to work)

### Additional Files

You will need

- a copy of `IGNORE_scheme_transpiled.js` put at `src/languages/scheme/web/IGNORE_scheme_transpiled.js`
- a copy of `IGNORE_scheme_debug.py` put at `src/web-server/IGNORE_scheme_debug.py`
- a copy of `IGNORE_secrets.py` [or failing that, a file that contains the line `SECRET="whatever"`] put at `src/web-server/IGNORE_secrets.py`

### Web Editor Backend Setup

Create a virtualenv

```sh
virtualenv -p python3 env
source env/bin/activate
pip install pipenv
cd dist/web
pipenv install # you may need to run sudo apt-get install libmysqlclient-dev or equivalent
cd ../..
```

Then run `python src/web-server/main.py` to start the python backend.

## Local Editor (experimental!)

To try, ensure that `python` is installed on your machine, and can be run with the `python3.6` command (will be made configurable in the future).

Then, run

```
yarn
yarn dist
yarn dev
```

and the editor will start.
