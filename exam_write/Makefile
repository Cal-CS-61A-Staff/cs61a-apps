.PHONY: dev
dev:
	export MODE=write; \
	export FLASK_APP=examtool_web_common/run_local; \
	export ENV=dev; \
	yarn run concurrently webpack "python examtool_web_common/run_local.py"
