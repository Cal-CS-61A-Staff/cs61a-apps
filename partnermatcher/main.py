from networkx import max_weight_matching, nx
import pandas as pd

from common.rpc.auth import write_spreadsheet

EMAIL_COL = "Email Address"
TIMEZONE_COL = "What is 8am PT (Berkeley Time) in your time?"
SKILL_COL = "How skillful a programmer do you consider yourself to be at this time?"
PNP_COL = "Are you taking CS 61A for a letter grade?"
WORDS_COL = "What are three words that describe your interests? "


def get_words(row):
    return [
        word.strip().lower()
        for word in sorted((row[WORDS_COL] or "").split(",")) + [""] * 3
    ]


def get_weight(row1, row2):
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
