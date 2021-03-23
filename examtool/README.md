## Overview

This is the CLI for the 61A `examtool`. To edit the various web apps, see the other `exam-*` folders in the `cs61a-apps` repo.

To install, run `pip install examtool[cli]`. To develop, create a virtualenv and run `pip install -e .[cli]`.

The CLI also requires `wget` and `pdflatex` to be installed and in your PATH.

To deploy exams to the server, you must be registered as an admin for your course at https://auth.apps.cs61a.org.

## Workflow

First, visit https://write.final.cs61a.org to write your exam, following [these instructions](https://github.com/Cal-CS-61A-Staff/cs61a-apps/blob/master/exam-write/README.md). When your exam is ready, export it as a JSON and place the JSON in a folder.

In that folder, run `examtool deploy` and select that JSON along with a roster CSV. When deployed, the exam will be accessible at https://exam.cs61a.org. Roster CSVs must have a header and the columns:
* `Email` - The email of a student
* `Deadline` - The due date of an exam for a particular student expressed as a Unix timestamp
* `No Watermark` - An optional column that is `1` if this student should not receive a watermarked exam (e.g. for DSP accomodations). Defaults to `0` if not specified.

You may wish to send exam PDFs to your students. To do so, run `examtool compile-all` to generate unique encrypted PDFs for each student. When they are all generated, run `examtool send` to email them to your students. Note that compilation requires `pdflatex` and `wget`. Compilation of watermarked PDFs also requires `inkscape`.

After your exam ends, run `examtool download` to download your student submissions as a single CSV and as PDFs to upload to Gradescope. To upload them to Gradescope, run `examtool gradescope-upload`.

To use an experimental autograder, run `gradescope-autograde` to download the exam, create the Gradescope assignment, upload them to Gradescope, add the outline to Gradescope, group all of the submissions, and finally apply grades to the groupings! Note you can use the same command to upload and autograde exams to the same Gradescope assignment, just ensure you use the `update` flag.

If you do not want the exam to be autograded, run `examtool download` to download your student submissions as a single CSV and as PDFs to upload to Gradescope. Use the `--via-html` flag to create formatted PDFs, or `--direct-pdf` to create plaintext PDFs. You must install `wkhtmltopdf` and place it in your PATH to create formatted PDFs.

To upload PDFs to Gradescope, run `examtool gradescope-upload`.

Note that if you ran alternate versions of your exam, it is possible that a student might have taken both versions (say, if they switched from the regular to the alternate version after filling out part of the regular version). To check for such students, run `examtool check-dupes`, and then manually decide which of their submissions should be uploaded to Gradescope.

Run `examtool loginas` to log in as a student and view their exam.

To identify cheating or recover from students losing their Internet connection, run `examtool logs` to see the full submission history of a particular student, or all students in the roster. 

Run `examtool save-logs` and then `examtool cheaters` to identify students who have used substituted words that did not occur in their exam, implying that they may be cheaters. Run `examtool identify-watermark` if you have a screenshot of a watermarked exam that you wish to identify. Run `examtool identify-keyword` if you wish to determine which students received exams with a particular keyword.
