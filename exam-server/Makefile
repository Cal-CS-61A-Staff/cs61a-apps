.PHONY: dev
dev:
	export GOOGLE_APPLICATION_CREDENTIALS=$(shell pwd)/../creds.json; \
	export FLASK_APP=examtool_web_common/run_local; \
	export ENV=dev; \
	yarn run concurrently "webpack --watch" "python run_local.py"
