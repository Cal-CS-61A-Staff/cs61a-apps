from networkx import max_weight_matching, nx
import pandas as pd

from common.rpc.auth import write_spreadsheet

EMAIL_COL = "Email Address"
TIMEZONE_COL = "What is 8am PT (Berkeley Time) in your time?"
SKILL_COL = "How skillful a programmer do you consider yourself to be at this time?"
PNP_COL = "Are you taking CS 61A for a letter grade?"
WORDS_COL = "What are three words that describe your interests? "


def get_words(row):
    """Returns a list of stripped, lowercase words from the WORDS_COL column
    of a student response row.

    :param row: One-dimensional array containing a student's responses to
    the partner matching questions.
    :type row: panda.Series

    :return: List of stripped, lowercase words from the WORDS_COL column
    of a student response row.
    """
    return [
        word.strip().lower()
        for word in sorted((row[WORDS_COL] or "").split(",")) + [""] * 3
    ]


def get_weight(row1, row2):
    """Calculates and returns the partner matching weight between two students 
    based on their responses. The higher the weight, the more the partner 
    matching algorithm will favor matching these two students together.

    :param row1: One-dimensional array containing the first student's responses 
    to the partner matching questions.
    :type row1: panda.Series
    :param row2: One-dimensional array containing the second student's responses 
    to the partner matching questions.
    :type row2: panda.Series

    :return: an int representing the partner matching weight between the student
    whose responses are in row1 and the students whose responses are in row2.
    """
    score = 0
    if row1[TIMEZONE_COL] == row2[TIMEZONE_COL]:
        score += 20
    if row1[SKILL_COL] == row2[SKILL_COL]:
        score += 10
    if row1[PNP_COL] == row2[PNP_COL]:
        score += 5
    words1 = get_words(row1)
    words2 = get_words(row2)
    score += sum(1 for word in words1 if word and word in words2)

    return score


data = pd.read_csv("alt-matcher/joined_data.csv", dtype=str).fillna("")
g = nx.Graph()

for i, row in data.iterrows():
    g.add_node(i)

for i, row1 in data.iterrows():
    for j, row2 in data.iterrows():
        if i >= j:
            continue
        g.add_edge(i, j, weight=get_weight(row1, row2))

matching = max_weight_matching(g)

csv = [["Student 1", "Student 2", "Timezone 1", "Timezone 2", "Words 1", "Words 2"]]

for i, j in matching:
    csv.append(
        [
            data.ix[i][EMAIL_COL],
            data.ix[j][EMAIL_COL],
            data.ix[i][TIMEZONE_COL],
            data.ix[j][TIMEZONE_COL],
            data.ix[i][WORDS_COL],
            data.ix[j][WORDS_COL],
        ]
    )

write_spreadsheet(
    url="https://docs.google.com/spreadsheets/d/1vpx-28ox2CNsyzbwrHLB9nCfiOZXksXp-jCgj21fNuw/",
    sheet_name="Sheet1",
    content=csv,
)
