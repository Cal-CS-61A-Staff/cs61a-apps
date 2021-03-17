"""
Developed by ThaumicMekanism [Stephan K.] - all credit goes to him!
"""
import contextlib
import sys
from typing import Callable, List

from multiprocessing.pool import ThreadPool
from tqdm.contrib import DummyTqdmFile

import examtool.api.download
from examtool.api.gradescope_upload import APIClient
from examtool.api.extract_questions import (
    extract_groups,
    extract_questions,
    extract_public,
)
from fullGSapi.api.login_tokens import LoginTokens
from fullGSapi.api.client import GradescopeClient
from fullGSapi.api.assignment_grader import (
    GS_Crop_info,
    GS_Outline,
    GS_assignment_Grader,
    GS_Outline_Question,
    GS_Question,
    GroupTypes,
    RubricItem,
    QuestionRubric,
)
import os
import time
from tqdm import tqdm

def_tqdm_args = {"dynamic_ncols": True}


@contextlib.contextmanager
def std_out_err_redirect_tqdm():
    orig_out_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = map(DummyTqdmFile, orig_out_err)
        yield orig_out_err[0]
    # Relay exceptions
    except Exception as exc:
        raise exc
    # Always restore sys.stdout/err if necessary
    finally:
        sys.stdout, sys.stderr = orig_out_err


class GradescopeGrader:
    def __init__(
        self,
        email: str = None,
        password: str = None,
        gs_login_tokens: LoginTokens = None,
        gs_login_tokens_path: str = None,
        simultaneous_jobs: int = 10,
        simultaneous_sub_jobs: int = 10,
    ):
        print(f"Setting up the Gradescope Grader...")
        entered_email_pwd = email is not None and password is not None

        logged_in = False

        if gs_login_tokens is None and not entered_email_pwd:
            gs_login_tokens = LoginTokens.load(gs_login_tokens_path)
            if gs_login_tokens is not None:
                logged_in = True
        else:
            print(
                "Ignoring current token file since you entered an email and password.\nLogging in with those credentials..."
            )
        if gs_login_tokens is None:
            gs_login_tokens = LoginTokens(path=gs_login_tokens_path)

        if entered_email_pwd:
            logged_in = gs_login_tokens.login(email, password)

        if not logged_in:
            gs_login_tokens.prompt_login(email=email)

        self.gs_login_tokens = gs_login_tokens
        self.gs_client = gs_login_tokens.gsFullapi
        self.gs_api_client = gs_login_tokens.gsAPI

        self.simultaneous_jobs = simultaneous_jobs
        self.simultaneous_sub_jobs = simultaneous_sub_jobs
        print(f"Finished setting up the Gradescope Grader")

    def main(
        self,
        exams: [str],
        out: str,
        name_question_id: str,
        sid_question_id: str,
        gs_class_id: str,
        gs_assignment_id: str = None,  # If none, we will create a class.
        gs_assignment_title: str = "Examtool Exam",
        emails: [str] = None,
        blacklist_emails: [str] = None,
        email_mutation_list: {str: str} = {},
        question_numbers: [str] = None,
        blacklist_question_numbers: [str] = None,
        custom_grouper_map: {
            str: Callable[[str, GS_Question, dict, dict], "QuestionGrouper"]
        } = None,
    ):
        if gs_assignment_title is None:
            gs_assignment_title = "Examtool Exam"
        if not exams:
            raise ValueError(
                "You must specify at least one exam you would like to upload!"
            )

        out = out or "out/export/" + exams[0]

        (
            exam_json,
            email_to_data_map,
            question_page_mapping,
        ) = self.fetch_and_export_examtool_exam_data(
            exams,
            out,
            name_question_id,
            sid_question_id,
            emails=emails,
            email_mutation_list=email_mutation_list,
        )

        # Remove blacklisted emails
        if blacklist_emails is not None:
            for bemail in blacklist_emails:
                email_to_data_map.pop(bemail, None)

        # Create assignment if one is not already created.
        if gs_assignment_id is None:
            print("Creating the gradescope assignment...")
            outline_path = f"{out}/OUTLINE.pdf"
            gs_assignment_id = self.create_assignment(
                gs_class_id, gs_assignment_title, outline_path
            )
            if not gs_assignment_id:
                raise ValueError(
                    "Did not receive a valid assignment id. Did assignment creation fail?"
                )
            print(f"Created gradescope assignment with id {gs_assignment_id}!")
        else:
            print(f"Using assignment ({gs_assignment_id}) which was already created!")

        # Lets now get the assignment grader
        grader: GS_assignment_Grader = self.get_assignment_grader(
            gs_class_id, gs_assignment_id
        )

        # Now that we have the assignment and outline pdf, lets generate the outline.
        print("Generating the examtool outline...")
        examtool_outline = ExamtoolOutline(
            grader,
            exam_json,
            [name_question_id, sid_question_id],
            question_page_mapping,
        )

        # Finally we need to upload and sync the outline.
        print("Uploading the generated outline...")
        self.upload_outline(grader, examtool_outline)

        # We can now upload the student submission since we have an outline
        print("Uploading student submissions...")
        failed_uploads = self.upload_student_submissions(
            out, gs_class_id, gs_assignment_id, emails=email_to_data_map.keys()
        )

        # Removing emails which failed to upload
        if failed_uploads:
            print(
                f"Removing emails which failed to upload. Note: These will NOT be graded! {failed_uploads}"
            )
            for email in tqdm(failed_uploads, **def_tqdm_args):
                email_to_data_map.pop(email)

        # For each question, group, add rubric and grade
        print("Setting the grade type for grouping for each question...")
        gs_outline = examtool_outline.get_gs_outline()
        self.set_group_types(gs_outline)

        # Fetch the student email to question id map
        print("Fetching the student email to submission id's mapping...")
        email_to_question_sub_id = grader.email_to_qids()

        # Check to see which emails may not be in the Gradescope roster and attempt to correct
        self.attempt_fix_unknown_gs_email(
            email_to_question_sub_id,
            email_to_data_map,
            name_question_id=name_question_id,
            sid_question_id=sid_question_id,
        )

        # Finally we can process each question
        self.process_questions(
            gs_outline,
            question_numbers,
            blacklist_question_numbers,
            email_to_data_map,
            email_to_question_sub_id,
            name_question_id,
            sid_question_id,
            custom_grouper_map,
        )

    def process_questions(
        self,
        gs_outline,
        question_numbers,
        blacklist_question_numbers,
        email_to_data_map,
        email_to_question_sub_id,
        name_question_id,
        sid_question_id,
        custom_grouper_map,
    ):
        def proc_q(d):
            qid, question = d
            if (
                question_numbers is not None
                and qid not in question_numbers
                or blacklist_question_numbers is not None
                and qid in blacklist_question_numbers
            ):
                tqdm.write(f"[{qid}]: Skipping!")
                return
            tqdm.write(f"[{qid}]: Processing question...")
            try:
                self.process_question(
                    qid,
                    question.get_gs_question(),
                    email_to_data_map,
                    email_to_question_sub_id,
                    name_question_id,
                    sid_question_id,
                    custom_grouper_map,
                )
            except Exception as e:
                import traceback

                traceback.print_exc(file=tqdm)
                tqdm.write(str(e))

        qi = list(gs_outline.questions_iterator())
        with ThreadPool(self.simultaneous_jobs) as p:
            list(
                tqdm(
                    p.imap_unordered(proc_q, qi),
                    total=len(qi),
                    desc="Questions Graded",
                    unit="Question",
                    **def_tqdm_args,
                )
            )

    def add_additional_exams(
        self,
        exams: [str],
        out: str,
        name_question_id: str,
        sid_question_id: str,
        gs_class_id: str,
        gs_assignment_id: str,
        emails: [str] = None,
        blacklist_emails: [str] = None,
        email_mutation_list: {str: str} = {},
        question_numbers: [str] = None,
        blacklist_question_numbers: [str] = None,
        custom_grouper_map: {
            str: Callable[[str, GS_Question, dict, dict], "QuestionGrouper"]
        } = None,
    ):
        """
        If emails is None, we will import the entire exam, if it has emails in it, it will only upload submissions
        from the students in the emails list contained in the exams list. If the student has submissions in multiple exams,
        the tool will warn you and ask which exam you would like to use as the student submission.
        """
        if not exams:
            raise ValueError(
                "You must specify at least one exam you would like to upload!"
            )
        if email_mutation_list is None:
            email_mutation_list = {}

        out = out or "out/export/" + exams[0]

        (
            exam_json,
            email_to_data_map,
            question_page_mapping,
        ) = self.fetch_and_export_examtool_exam_data(
            exams,
            out,
            name_question_id,
            sid_question_id,
            emails=emails,
            email_mutation_list=email_mutation_list,
        )

        # Remove blacklisted emails
        if blacklist_emails is not None:
            for bemail in blacklist_emails:
                email_to_data_map.pop(bemail, None)

        # Lets now get the assignment grader
        grader: GS_assignment_Grader = self.get_assignment_grader(
            gs_class_id, gs_assignment_id
        )

        # Now that we have the assignment and outline pdf, lets generate the outline.
        print("Generating the examtool outline...")
        examtool_outline = ExamtoolOutline(
            grader,
            exam_json,
            [name_question_id, sid_question_id],
            question_page_mapping,
        )

        # Merge the outline with the existing one
        outline = grader.get_outline()
        if not outline:
            raise ValueError("Failed to fetch the existing outline")
        examtool_outline.merge_gs_outline_ids(outline)

        # We can now upload the student submission since we have an outline
        print("Uploading student submissions...")
        failed_uploads = self.upload_student_submissions(
            out, gs_class_id, gs_assignment_id, emails=email_to_data_map.keys()
        )

        # Removing emails which failed to upload
        if failed_uploads:
            print(
                f"Removing emails which failed to upload. Note: These will NOT be graded! {failed_uploads}"
            )
            for email in failed_uploads:
                email_to_data_map.pop(email)

        # Fetch the student email to question id map
        print("Fetching the student email to submission id's mapping...")
        email_to_question_sub_id = grader.email_to_qids()

        # Check to see which emails may not be in the Gradescope roster and attempt to correct
        self.attempt_fix_unknown_gs_email(
            email_to_question_sub_id,
            email_to_data_map,
            name_question_id=name_question_id,
            sid_question_id=sid_question_id,
        )

        gs_outline = examtool_outline.get_gs_outline()

        # Finally we can process each question
        self.process_questions(
            gs_outline,
            question_numbers,
            blacklist_question_numbers,
            email_to_data_map,
            email_to_question_sub_id,
            name_question_id,
            sid_question_id,
            custom_grouper_map,
        )

    def fetch_and_export_examtool_exam_data(
        self,
        exams: [str],
        out: str,
        name_question_id: str,
        sid_question_id: str,
        emails: [str] = None,
        email_mutation_list: {str: str} = {},
    ):
        """
        Fetches the submissions from the exams in the exams list.
        If the emails list is None, it will fetch all emails, if it has emails in it, it will only return data for those emails.
        The mutation step occurres after the specific emails selection stage if applicable.
        The mutation list comes in the form of current email to new email.

        Returns:
        exam_json - The json of the exam
        email_to_data_map - the mapping of emails to their data.
        """
        if not exams:
            raise ValueError(
                "You must specify at least one exam you would like to upload!"
            )
        if email_mutation_list is None:
            email_mutation_list = {}

        print("Downloading exams data...")
        exam_json = None
        email_to_data_map = {}
        email_to_exam_map = {}

        first_exam = True
        for exam in exams:
            (
                tmp_exam_json,
                tmp_template_questions,
                tmp_email_to_data_map,
                tmp_total,
            ) = examtool.api.download.download(exam)

            # Choose only the emails we want to keep.
            if emails:
                for email in list(tmp_email_to_data_map.keys()):
                    if email not in emails:
                        tmp_email_to_data_map.pop(email, None)

            # Next, we want to mutate any emails
            for orig_email, new_email in email_mutation_list.items():
                if orig_email not in tmp_email_to_data_map:
                    print(
                        f"WARNING: Could not perform mutation on email {orig_email} (to {new_email}) because it does not exist in the data map!"
                    )
                    continue
                if new_email in tmp_email_to_data_map:
                    print(
                        f"Could not mutate email {new_email} (from {orig_email}) as the original email is already in the data map!"
                    )
                    continue
                tmp_email_to_data_map[new_email] = tmp_email_to_data_map.pop(orig_email)

            # Finally, we should merge together the student responses.
            for email, data in tmp_email_to_data_map.items():
                if email in email_to_data_map:
                    print(
                        f"WARNING: Student with email {email} submitted to multiple exams!"
                    )

                    def prompt_q():
                        input_data = None
                        while not input_data:
                            print(
                                f"Student's current responses are from {email_to_exam_map[email]}, would you like to use {exam} instead?"
                            )
                            input_data = input("[y/n]> ")
                            if input_data.lower() in ["y", "yes"]:
                                return True
                            if input_data.lower() in ["n", "no"]:
                                return False
                            print("Please type yes or no!")

                    if not prompt_q():
                        continue
                email_to_exam_map[email] = exam
                email_to_data_map[email] = data

            question_page_mapping = examtool.api.download.get_question_to_page_mapping(
                tmp_template_questions,
                exam,
                out,
                name_question_id,
                sid_question_id,
            )

            print(f"[{exam}]: Exporting exam pdfs...")

            self.export_exam(
                tmp_template_questions,
                tmp_email_to_data_map,
                tmp_total,
                exam,
                out,
                name_question_id,
                sid_question_id,
                include_outline=first_exam,
            )

            # Set global data for the examtool
            if first_exam:
                first_exam = False
                exam_json = tmp_exam_json

        # Lets finally clean up the student responses
        self.cleanse_student_response_data(email_to_data_map)

        return exam_json, email_to_data_map, question_page_mapping

    def attempt_fix_unknown_gs_email(
        self,
        email_to_question_sub_id,
        email_to_data_map,
        name_question_id,
        sid_question_id,
    ):
        def prompt_fix(old_email, name, sid):
            input_data = None
            while not input_data:
                print(
                    f"Could not find {old_email} (name: {name}; sid: {sid}) in Gradescope! Please enter the Gradescope email of the student or `skip` to remove this student from autograding."
                )
                input_data = input("> ")
                if "@" in input_data.lower():
                    return input_data
                if input_data.lower() in ["n", "no", "skip"]:
                    return False
                print(
                    "The input is not a valid email (you are missing the `@`)! If you would like to skip, type `skip` or `no`."
                )

        remove_email = ["DUMMY"]
        map_email = {}
        while remove_email or map_email:
            remove_email = []
            map_email = {}
            for email, data in email_to_data_map.items():
                if email not in email_to_question_sub_id:
                    responses = data["responses"]
                    name = responses.get(name_question_id, None)
                    sid = responses.get(sid_question_id, None)
                    new_email = prompt_fix(email, name, sid)
                    if new_email:
                        map_email[email] = new_email
                    else:
                        print(
                            f"Skipping {email}! This will remove the email from the data map."
                        )
                        remove_email.append(email)
            for email, new_email in map_email.items():
                email_to_data_map[new_email] = email_to_data_map.pop(email)
            for email in remove_email:
                email_to_data_map.pop(email)

    def cleanse_student_response_data(self, email_to_data_map: dict):
        for email, data in email_to_data_map.items():
            std_questions = data["student_questions"]
            std_responses = data["responses"]
            for question in std_questions:
                qid = question["id"]
                if qid not in std_responses:
                    std_responses[qid] = (
                        []
                        if question["type"] in ["multiple_choice", "select_all"]
                        else ""
                    )

    def export_exam(
        self,
        template_questions,
        email_to_data_map,
        total,
        exam,
        out,
        name_question_id,
        sid_question_id,
        include_outline=True,
    ):
        examtool.api.download.export(
            template_questions,
            email_to_data_map,
            total,
            exam,
            out,
            name_question_id,
            sid_question_id,
            include_outline=include_outline,
        )

    def create_assignment(self, gs_class_id: str, gs_title: str, outline_path: str):
        assignment_id = self.gs_client.create_exam(gs_class_id, gs_title, outline_path)
        if not assignment_id:
            print("Failed to create the exam! Make sure it has a unique title.")
            return
        return assignment_id

    def get_assignment_grader(
        self, gs_class_id: str, assignment_id: str
    ) -> GS_assignment_Grader:
        return self.gs_client.get_assignment_grader(gs_class_id, assignment_id)

    def upload_outline(
        self, grader: GS_assignment_Grader, examtool_outline: "ExamtoolOutline"
    ):
        outline = grader.update_outline(examtool_outline.get_gs_outline())
        if not outline:
            raise ValueError("Failed to upload or get the outline")
        examtool_outline.merge_gs_outline_ids(outline)

    def upload_student_submissions(
        self, out: str, gs_class_id: str, assignment_id: str, emails: [str] = None
    ):
        failed_emails = []
        email_files = []
        for file_name in os.listdir(out):
            if "@" not in file_name:
                continue
            student_email = file_name[:-4]
            if emails and student_email not in emails:
                continue
            email_files.append((file_name, student_email))
        with std_out_err_redirect_tqdm() as orig_stdout:
            # for file_name, student_email in tqdm(
            #     email_files, file=orig_stdout, unit="Submission", **def_tqdm_args
            # ):
            def func(tup):
                file_name, student_email = tup
                if not self.gs_api_client.upload_pdf_submission(
                    gs_class_id,
                    assignment_id,
                    student_email,
                    os.path.join(out, file_name),
                ):
                    failed_emails.append(student_email)

            with ThreadPool(self.simultaneous_jobs) as p:
                list(
                    tqdm(
                        p.imap_unordered(func, email_files),
                        total=len(email_files),
                        file=orig_stdout,
                        unit="Submission",
                        **def_tqdm_args,
                    )
                )
        return failed_emails

    def set_group_types(self, outline: GS_Outline, debug=True):
        questions = list(outline.questions_iterator())
        with std_out_err_redirect_tqdm() as orig_stdout:
            # for qid, question in tqdm(
            #     questions, file=orig_stdout, unit="Question", **def_tqdm_args
            # ):
            #     self.set_group_type(question)
            def sgt(q):
                qid, question = q
                self.set_group_type(question)

            with ThreadPool(self.simultaneous_jobs) as p:
                list(
                    tqdm(
                        p.imap_unordered(sgt, questions),
                        total=len(questions),
                        file=orig_stdout,
                        unit="Question",
                        **def_tqdm_args,
                    )
                )

    def set_group_type(self, o_question: GS_Outline_Question):
        question_type = o_question.data.get("type")
        q = o_question.get_gs_question()
        q_type = GroupTypes.complex
        if question_type in ["select_all", "multiple_choice"]:
            q_type = GroupTypes.mc
        # if question_type in ["long_answer", "long_code_answer"]:
        #     q_type = GroupTypes.non_grouped
        return q.set_group_type(q_type)

    def process_question(
        self,
        qid: str,
        question: GS_Question,
        email_to_data_map: dict,
        email_to_question_sub_id_map: dict,
        name_question_id: str,
        sid_question_id: str,
        custom_grouper_map: {
            str: Callable[[str, GS_Question, dict, dict], "QuestionGrouper"]
        },
    ):
        # Group questions
        if question.data.get("id") in [name_question_id, sid_question_id]:
            tqdm.write("Skipping grouping of an id question!")
            return
        tqdm.write(f"[{qid}]: Grouping...")
        groups = self.group_question(
            qid,
            question,
            email_to_data_map,
            email_to_question_sub_id_map,
            custom_grouper_map,
        )
        if groups:
            # Group answers
            tqdm.write(f"[{qid}]: Syncing groups on gradescope...")
            self.sync_groups_on_gradescope(qid, question, groups)
            tqdm.write(f"[{qid}]: Syncing rubric items...")
            rubric = self.sync_rubric(qid, question, groups)
            # in here, add check to see if qid is equal to either name or sid q id so we do not group those.
            tqdm.write(f"[{qid}]: Applying grades for each group...")
            self.grade_question(qid, question, rubric, groups)
        else:
            tqdm.write(f"[{qid}]: Failed to group question {qid}!")

    def group_question(
        self,
        qid: str,
        question: GS_Question,
        email_to_data_map: dict,
        email_to_question_sub_id_map: dict,
        custom_grouper_map: {
            str: Callable[[str, GS_Question, dict, dict], "QuestionGrouper"]
        },
    ):
        if custom_grouper_map is not None:
            examtool_qid = question.data.get("id")
            if examtool_qid in custom_grouper_map:
                return custom_grouper_map[examtool_qid](
                    qid, question, email_to_data_map, email_to_question_sub_id_map
                )
            if qid in custom_grouper_map:
                return custom_grouper_map[qid](
                    qid, question, email_to_data_map, email_to_question_sub_id_map
                )
        # Default handler
        qtype = question.data.get("type")
        if qtype in ["multiple_choice", "select_all"]:
            return self.group_mc_question(
                qid, question, email_to_data_map, email_to_question_sub_id_map
            )
        elif qtype in ["short_answer", "short_code_answer"]:
            return self.group_short_ans_question(
                qid, question, email_to_data_map, email_to_question_sub_id_map
            )
        elif qtype in ["long_answer", "long_code_answer"]:
            return self.group_long_ans_question(
                qid, question, email_to_data_map, email_to_question_sub_id_map
            )
        else:
            tqdm.write(
                f"Unsupported question type {qtype} for question {question.data}!"
            )
            return None

    def group_mc_question(
        self,
        qid: str,
        question: GS_Question,
        email_to_data_map: dict,
        email_to_question_sub_id_map: dict,
        custom_rubric_weights_fn: Callable[
            [GS_Question, List[str], List[bool]], List[float]
        ] = None,
    ):
        data = question.data
        # This is a list of correct options from left (top) to right (bottom)
        correct_seq = []
        seq_name = []
        solution_options = data.get("solution", {})
        if solution_options is not None:
            solution_options = solution_options.get("options", [])
        if solution_options is None:
            solution_options = []
        all_options = [option.get("text") for option in data.get("options", [])]
        for option in all_options:
            correct_seq.append(option in solution_options)
            seq_name.append(option)

        # Add blank option
        correct_seq.append(None)
        seq_name.append("Blank")
        # Add student did not receive this question
        correct_seq.append(None)
        seq_name.append("Student did not receive this question")

        rubric_weights = (
            self.get_basic_rubric_scores(question, seq_name, correct_seq)
            if custom_rubric_weights_fn is None
            else custom_rubric_weights_fn(question, seq_name, correct_seq)
        )

        groups = QuestionGrouper(
            question,
            rubric=[
                RubricItem(description=item[0], weight=item[1])
                for item in zip(seq_name, rubric_weights)
            ],
        )

        def list_to_str(l):
            s = ""
            for item in l:
                s += str(int(item))
            return s

        eqid = question.data["id"]
        for email, data in email_to_data_map.items():
            responses = data.get("responses", {})
            response = responses.get(eqid)
            selection = [False] * len(correct_seq)
            if response is None:
                selection[-1] = True
            elif response == []:
                selection[-2] = True
            else:
                if not isinstance(response, list):
                    response = [response]
                for i, option in enumerate(all_options):
                    selection[i] = option in response

            s = list_to_str(selection)
            sid = email_to_question_sub_id_map[email][qid]
            if s not in groups:
                groups.add_group(QuestionGroup(s, selection))
            groups.get_group(s).add_sid(sid)
        return groups

    def group_short_ans_question(
        self,
        qid: str,
        question: GS_Question,
        email_to_data_map: dict,
        email_to_question_sub_id_map: dict,
        lower_check: bool = True,
        custom_rubric_weights_fn: Callable[
            [GS_Question, List[str], List[bool]], List[float]
        ] = None,
        strip_md_from_sol: bool = True,
    ):
        data = question.data
        # This is a list of correct options from left (top) to right (bottom)
        solution = data.get("solution", {})
        if solution is not None:
            solution = solution.get("solution", {})
            if solution is not None:
                solution = solution.get("text")
        if not solution:
            tqdm.write(
                f"[{qid}]: No solution defined for this question! Only grouping blank and std did not receive."
            )
            solution = "Correct"
        correct_seq = [True]
        seq_name = [solution]

        # Add a wrong option
        correct_seq.append(None)
        seq_name.append("Incorrect")
        # Add blank option
        correct_seq.append(None)
        seq_name.append("Blank")
        # Add student did not receive this question
        correct_seq.append(None)
        seq_name.append("Student did not receive this question")

        rubric_weights = (
            self.get_basic_rubric_scores(question, seq_name, correct_seq)
            if custom_rubric_weights_fn is None
            else custom_rubric_weights_fn(question, seq_name, correct_seq)
        )

        groups = QuestionGrouper(
            question,
            rubric=[
                RubricItem(description=item[0], weight=item[1])
                for item in zip(seq_name, rubric_weights)
            ],
        )

        # Process solution
        if lower_check:
            sol = solution.strip().lower()
        else:
            sol = solution.strip()

        if strip_md_from_sol:

            def strip_part(text, boundary):
                if text.startswith(boundary) and text.endswith(boundary):
                    blen = len(boundary)
                    return (text[blen:-blen], True)
                else:
                    return (text, False)

            sol, replaced = strip_part(sol, "$")

            if not replaced:
                sol, replaced = strip_part(sol, "```")

                if not replaced:
                    sol, replaced = strip_part(sol, "`")

        eqid = question.data["id"]
        for email, data in email_to_data_map.items():
            responses = data.get("responses", {})
            response = responses.get(eqid)
            selection = [False] * len(correct_seq)
            if response is None:
                selection[-1] = True
                response = "Student did not receive this question"
            elif response == "":
                selection[-2] = True
                response = "Blank"
            else:
                if solution is not None:
                    same = None
                    if lower_check:
                        same = response.lower().strip() == sol
                    else:
                        same = response.strip() == sol
                    if same:
                        selection[0] = True
                    else:
                        selection[1] = True

            sid = email_to_question_sub_id_map[email][qid]
            if response not in groups:
                groups.add_group(QuestionGroup(response, selection))
            groups.get_group(response).add_sid(sid)
        return groups

    def group_long_ans_question(
        self,
        qid: str,
        question: GS_Question,
        email_to_data_map: dict,
        email_to_question_sub_id_map: dict,
    ):
        """
        We will only be grouping students who did not get the question or left it blank.
        """
        data = question.data
        # This is a list of correct options from left (top) to right (bottom)
        correct_seq = [True]
        seq_name = ["Correct"]

        # Add blank option
        correct_seq.append(None)
        seq_name.append("Blank")
        # Add student did not receive this question
        correct_seq.append(None)
        seq_name.append("Student did not receive this question")

        rubric_weights = self.get_long_ans_rubric_scores(
            question, seq_name, correct_seq
        )

        groups = QuestionGrouper(
            question,
            rubric=[
                RubricItem(description=item[0], weight=item[1])
                for item in zip(seq_name, rubric_weights)
            ],
        )

        group_blank = QuestionGroup("Blank", [False, True, False])
        groups.add_group(group_blank)

        group_sdnrtq = QuestionGroup(
            "Student did not receive this question", [False, False, True]
        )
        groups.add_group(group_sdnrtq)

        eqid = question.data["id"]
        for email, data in email_to_data_map.items():
            responses = data.get("responses", {})
            response = responses.get(eqid)
            if not response:
                sid = email_to_question_sub_id_map[email][qid]
                if response is None:
                    group_sdnrtq.add_sid(sid)
                elif response == "":
                    group_blank.add_sid(sid)
        return groups

    def sync_groups_on_gradescope(
        self, qid: str, question: GS_Question, groups: "QuestionGrouper"
    ):
        """
        Groups is a list of name, submission_id, selected answers
        """
        failed_groups_names = []
        i = 1
        failed = False
        while not question.is_grouping_ready():
            timeout = 5
            tqdm.write(
                f"[{qid}]: Question grouping not ready! Retrying in {timeout} seconds!"
            )
            time.sleep(timeout)
        #     print(f"[{qid}]: Question grouping not ready! Retrying in {timeout} seconds" + (" " * timeout), end="\r")
        #     for i in range (timeout):
        #         print(f"[{qid}]: Question grouping not ready! Retrying in {timeout} seconds" + ("." * (1 + i)), end="\r")
        #         time.sleep(1)
        #     failed = True
        # if failed:
        #     print("")
        gradescope_groups = question.get_groups()

        def all_zeros(s: str):
            return s and all(v == "0" for v in s)

        def set_group(group, gs_group):
            group.set_id(gs_group.get("id"))

        for group in groups.get_groups():
            g_name = group.get_name()
            for gs_group in gradescope_groups:
                if gs_group["question_type"] == "mc":
                    # The question type is mc so lets group by the internal mc
                    if g_name == "Blank":
                        # This is the blank group, lets use the internal label to group
                        if all_zeros(gs_group["internal_title"]):
                            set_group(group, gs_group)
                    else:
                        flip_g_name = g_name[:-2][::-1]
                        if gs_group["internal_title"] is not None:
                            if (
                                flip_g_name == gs_group["internal_title"]
                                and g_name[len(g_name) - 1] != "1"
                            ):
                                set_group(group, gs_group)
                        else:
                            if g_name == gs_group["title"]:
                                set_group(group, gs_group)
                else:
                    # The question type is not mc so we should group on title and internal title for blank.
                    # The internal title should only say Blank for default blank grouped submissions.
                    # We then check the normal title if this is not true
                    if (
                        g_name == gs_group["internal_title"]
                        or g_name == gs_group["title"]
                    ):
                        set_group(group, gs_group)

        def submit_group(group, question, failed_groups_names, max_attempts):
            attempt = 1
            g_name = group.get_name()
            sids = group.get_sids()
            if not sids:
                # We do not want to create groups which no questions exist.
                return
            group_id = group.get_id()
            while attempt < max_attempts:
                if not group_id:
                    group_id = question.add_group(g_name)
                if group_id is None:
                    attempt += 1
                    time.sleep(1)
                    return
                if not question.group_submissions(group_id, sids):
                    tqdm.write(
                        f"[{qid}]: Failed to group submissions to {group_id}. SIDS: {sids}"
                    )
                    failed_groups_names.append(g_name)
                break
            else:
                tqdm.write(f"[{qid}]: Failed to create group for {g_name}! ({groups})")
                failed_groups_names.append(g_name)

        # max_attempts = 5
        # for group in tqdm(
        #     groups.get_groups(),
        #     desc=f"[{qid}]: Syncing Groups",
        #     unit="Group",
        #     **def_tqdm_args,
        # ):
        #     submit_group(group, question, failed_groups_names, max_attempts)

        gps = groups.get_groups()

        def sg(g):
            submit_group(g, question, failed_groups_names, 5)

        with ThreadPool(self.simultaneous_sub_jobs) as p:
            list(
                tqdm(
                    p.imap_unordered(sg, gps),
                    total=len(gps),
                    desc=f"[{qid}]: Syncing Groups",
                    unit="Group",
                    **def_tqdm_args,
                )
            )

        # This is to decrease down stream errors
        for failed_group_name in failed_groups_names:
            groups.remove(failed_group_name)

    @classmethod
    def get_basic_rubric_scores(cls, question: GS_Question, group_names, correct_seq):
        scores = []
        num_correct = sum([1 for correct in correct_seq if correct])
        num_choices = sum([1 for correct in correct_seq if correct is not None])
        points = question.data.get("points", 1)
        if points is None:
            points = 1
        rubric_weight = 0
        if num_correct != 0:
            rubric_weight = (1 / num_correct) * points
        for correct in correct_seq:
            if correct is None:
                scores.append(0)
            else:
                if correct:
                    scores.append(rubric_weight)
                else:
                    scores.append(-rubric_weight)
        return scores

    @classmethod
    def get_long_ans_rubric_scores(
        cls, question: GS_Question, group_names, correct_seq
    ):
        return [0] * len(correct_seq)

    def sync_rubric(
        self, qid: str, question: GS_Question, groups: "QuestionGrouper"
    ) -> QuestionRubric:
        rubric = QuestionRubric(question)
        if len(groups) == 0:
            return rubric

        qrubric: [RubricItem] = groups.get_rubric()

        if len(rubric) == 1:
            default_rubric_item = rubric.get_rubric_items()[0]
            if default_rubric_item.description == "Correct":
                first_item = qrubric[0]
                if not rubric.update_rubric_item(
                    default_rubric_item,
                    description=first_item.description,
                    weight=first_item.weight,
                ):
                    tqdm.write(
                        f'[{qid}]: Failed to update default "Correct" rubric item!'
                    )
                # qrubric.remove(first_item)

        existing_rubric_items = rubric.get_rubric_items()
        existing_rubric_items_desc = [
            item.description for item in existing_rubric_items
        ]

        for rubric_item in tqdm(
            qrubric, desc=f"[{qid}]: Syncing Rubric", unit="Rubric", **def_tqdm_args
        ):
            if rubric_item.description not in existing_rubric_items_desc:
                rubric.add_rubric_item(rubric_item)

        return rubric

    def grade_question(
        self, qid: str, question: GS_Question, rubric: QuestionRubric, groups: dict
    ):
        question_data = question.get_question_info()
        sub_id_mapping = {str(sub["id"]): sub for sub in question_data["submissions"]}
        # for group in tqdm(
        #     groups.get_groups(), desc=f"[{qid}]: Grading", unit="Group", **def_tqdm_args
        # ):
        def sg(group):
            group_sel = group.get_selected_items()
            group_sids = group.get_sids()
            if len(group_sids) > 0:
                sid = group_sids[0]
                if not sub_id_mapping[str(sid)]["graded"]:
                    if not rubric.grade(sid, group_sel, save_group=True):
                        tqdm.write(
                            f"[{qid}]: Failed to grade group {group.get_name()}!"
                        )

        gps = groups.get_groups()
        with ThreadPool(self.simultaneous_sub_jobs) as p:
            list(
                tqdm(
                    p.imap_unordered(sg, gps),
                    total=len(gps),
                    desc=f"[{qid}]: Grading",
                    unit="Group",
                    **def_tqdm_args,
                )
            )


class ExamtoolOutline:
    name_region = GS_Crop_info(1, 2.4, 11.4, 99, 18.8)
    sid_region = GS_Crop_info(1, 2.4, 18.9, 99, 28.7)

    def __init__(
        self,
        grader: GS_assignment_Grader,
        exam_json: dict,
        id_question_ids: List[str],
        question_page_mapping: List[int],
    ):
        self.exam_json = exam_json
        self.gs_number_to_exam_q, self.gs_outline = self.generate_gs_outline(
            grader, exam_json, id_question_ids, question_page_mapping
        )

    def get_gs_crop_info(self, page, question=None):
        return GS_Crop_info(page, 4, 4, 96, 96)

    def question_to_gso_question(
        self, grader: GS_assignment_Grader, page, question: dict
    ) -> GS_Outline_Question:
        weight = question.get("points")
        if not weight:
            weight = 0
        return GS_Outline_Question(
            grader,
            None,
            [self.get_gs_crop_info(page, question=question)],
            title=question.get("name", ""),
            weight=weight,
        )

    def generate_gs_outline(
        self,
        grader: GS_assignment_Grader,
        exam_json: dict,
        id_question_ids: [str],
        question_page_mapping: List[int],
    ):
        gs_number_to_exam_q = {}
        questions = []

        page = 0  # Page 1 is an info page

        qid = 1
        if exam_json.get("public"):
            prev_page = 0
            pg = GS_Outline_Question(
                grader,
                None,
                [self.get_gs_crop_info(page, exam_json.get("public"))],
                title="Public",
                weight=0,
            )
            sqid = 1
            for question in extract_public(exam_json):
                question_id = question.get("id")
                if question_id in id_question_ids:
                    print(f"Skipping {question_id} as it is an id question.")
                    page += 1  # Still need to increment this as it is still on the exam pdf.
                    continue
                pg.add_child(
                    self.question_to_gso_question(
                        grader, question_page_mapping[page], question
                    )
                )
                gs_number_to_exam_q[f"{qid}.{sqid}"] = question
                sqid += 1
                page += 1
            if page != prev_page and len(pg.children) > 0:
                questions.append(pg)
                qid += 1

        for group in extract_groups(exam_json):
            prev_page = page
            weight = group.get("points", "0")
            if not weight:
                weight = 0
            g = GS_Outline_Question(
                grader,
                None,
                [self.get_gs_crop_info(question_page_mapping[page], group)],
                title=group.get("name", ""),
                weight=weight,
            )
            sqid = 1
            for question in extract_questions(
                group, extract_public_bool=False, top_level=False
            ):
                g.add_child(
                    self.question_to_gso_question(
                        grader, question_page_mapping[page], question
                    )
                )
                gs_number_to_exam_q[f"{qid}.{sqid}"] = question
                sqid += 1
                page += 1
            if page != prev_page:
                questions.append(g)
                qid += 1

        outline = GS_Outline(self.name_region, self.sid_region, questions)
        return (gs_number_to_exam_q, outline)

    def get_gs_outline(self):
        return self.gs_outline

    def merge_gs_outline_ids(self, outline: GS_Outline):
        self.gs_outline = outline
        for qnum, q in outline.questions_iterator():
            q.data = self.gs_number_to_exam_q[qnum]

    def questions_iterator(self):
        yield from self.gs_outline.questions_iterator()


class QuestionGroup:
    def __init__(self, name: str, selected_rubric_items: [bool], gid: str = None):
        self.name = name
        self.selected_rubric_items = (
            selected_rubric_items  # Bool array of selected items.
        )
        self.gid = gid
        self.sids = set()

    def get_name(self):
        return self.name

    def get_id(self):
        return self.gid

    def set_id(self, gid: str):
        self.gid = gid

    def get_sids(self):
        return list(self.sids)

    def add_sid(self, sid: str):
        self.sids.add(sid)

    def add_sids(self, sids: [str]):
        self.sids = self.sids.union(sids)

    def get_selected_items(self):
        return self.selected_rubric_items


class QuestionGrouper:
    def __init__(
        self,
        question: GS_Question,
        rubric: [RubricItem],  # This is a list of rubric items.
        groups: {str: QuestionGroup} = None,
    ):
        self.groups = groups
        if not self.groups:
            self.groups = {}
        self.question = question
        self.rubric = rubric

    def get_groups(self):
        return self.groups.values()

    def get_group(self, name):
        return self.groups.get(name)

    def add_group(self, group: QuestionGroup):
        self.groups[group.get_name()] = group

    def remove(self, group_name):
        for g in self.groups:
            if g.get_name() == group_name:
                self.groups.remove(g)
                return

    def __len__(self):
        return len(self.groups)

    def get_rubric(self) -> [RubricItem]:
        return self.rubric

    def __contains__(self, key):
        return key in self.groups
