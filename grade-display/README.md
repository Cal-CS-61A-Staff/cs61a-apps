# Grade Display Scripts
This folder contains up-to-date versions of the scripts and config used to display grades on howamidoing.cs61a.org.

To change how grades are processed before being uploaded to howamidoing, take a look at `assemble.py`. To change how grades are exported from Gradescope and the relevant columns are saved, take a look at `gs_export.py`. To change how grades are displayed on howamidoing, take a look at `config.json`.

## Setting Up
1. In this folder, run `python3 -m venv env` to create a virtual environment.
2. Activate the environment (on \*nix machines, this implies running `source env/bin/activate`).
3. Install the required Python libraries by running `pip3 install -r requirements.txt`.
4. Run whichever scripts you need!
5. Deactivate the environment by running `deactivate`.

## Updating Grades
1. Export an up-to-date roster from Okpy. Save as `data/roster.csv`.
2. Export grades from Okpy (see "Exporting from Okpy").
3. Export grades from Gradescope if needed (see "Exporting from Gradescope").
4. Export grades from the Tutorials tool if needed (see "Exporting from Sections").
4. Run `python3 assemble.py` to combine the roster with relevant grades and optionally upload the result to howamidoing. The result will also be saved to `data/grades.csv`.

## Exporting from Okpy
1. In `okpy_export.py`, make sure the `COURSE_CODE` and `SEMESTER` correspond to the correct Okpy course code and offering.
2. Run `python3 okpy_export.py`. A browser window will pop up, asking you to authorize Okpy to generate an OAuth code. Authorize the application in order to receive a code, which will either be read by the script automatically or will need to be pasted in. This will generate an access token that the script will use to access grades on Okpy.
3. Results will be saved to `data/okpy_grades.csv`. If the `--debug` flag is used, the script will run on `localhost:5000` instead and results will be saved to `data/okpy_test.csv`.

## Exporting from Gradescope
1. In `gs_export.py`, make sure the `COURSE_CODE` corresponds to the correct Gradescope course.
2. Also in `gs_export.py`, make sure the `ASSIGNMENTS` dictionary contains your assignment shortcodes properly mapped to Gradescope assignment codes.
3. If you want to avoid typing in your credentials each time you use this script, create a `credentials.txt` file with two lines: the first should be your Gradescope email address, and the second should be your Gradescope password.
4. Run `python3 gs_export.py` and enter your assignment shortcode when prompted (or run `python3 gs_export.py <shortcode>`).
5. The export will be saved to `data/<shortcode>.csv`.

## Exporting from Sections
1. Run `python3 sections_export.py`.
2. The export will be saved to `data/tutorials.csv`.

## Configuring Howamidoing
1. Make your changes in `config.json`.
2. Drag and drop `config.json` onto howamidoing.cs61a.org.
3. Wait for the "Upload Succeeded!" dialog to appear.

## Streamlining Updates
1. Create a Python script and import all the features you need to use (`okpy_export`, `gs_export`, `sections_export`, `assemble`.
2. Call the `export` function *one* for Okpy.
3. Call the `export` function for as many Gradescope assignments you need to export, passing in the shortcode for each assignment one by one.
4. Call the `export` function *once* for the Tutorials tool.
5. Call the `assemble` function *once*, with an optional boolean flag for whether or not the script should update Howamidoing (this is `True` by default).

