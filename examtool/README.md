## Overview
This is the CLI for the 61A `examtool`. To edit the various web apps, see the `examtool-web` repo.

To install, run `pip install examtool[cli]`. To develop, create a virtualenv and run `pip install -e .`. 

The CLI also requires `pdflatex` to be installed and in your PATH.

To deploy exams to the server, you must be registered as an admin for your course at https://auth.apps.cs61a.org.

## Workflow
First, visit https://write.final.cs61a.org to write your exam, following instructions in the README of `examtool-web/apps/write` folder. When your exam is ready, export it as a JSON and place the JSON in a folder.

In that folder, run `examtool deploy` and select that JSON along with a roster CSV. When deployed, the exam will be accessible at https://exam.cs61a.org.

You may wish to send exam PDFs to your students. To do so, run `examtool compile-all` to generate unique encrypted PDFs for each student. When they are all generated, run `examtool send` to email them to your students.
 
 After your exam ends, you can run `gradescope-autograde` to download the exam, create the Gradescope assignment, upload them to Gradescope, add the outline to Gradescope, group all of the submissions, and finally apply grades to the groupings! Note you can use the same command to upload and autograde exams to the same Gradescope assignment, just ensure you use the `update` flag.
 
 If you do not want the exam to be autograded, run `examtool download` to download your student submissions as a single CSV and as PDFs to upload to Gradescope. To upload them to Gradescope, run `examtool gradescope-upload`. 
 
 Note that if you ran alternate versions of your exam, it is possible that a student might have taken both versions (say, if they switched from the regular to the alternate version after filling out part of the regular version). To check for such students, run `examtool check-dupes`, and then manually decide which of their submissions should be uploaded to Gradescope.
 
 To identify cheating or recover from students losing their Internet connection, run `examtool logs` to see the full submission history of a particular student, or all students in the roster.
