# CONFIG SCRAMBLE_GROUPS 1

# CONFIG WATERMARK 50

# CONFIG SCRAMBLE_OPTIONS

# BEGIN PUBLIC Preliminaries

You can complete and submit these questions before the exam starts.

# BEGIN QUESTION

What is your full name?

# INPUT SHORT_ANSWER

# END QUESTION

# BEGIN QUESTION

What is your student ID number? A regex restricts inputs to numerical responses only.

# INPUT SHORT_CODE_ANSWER [0-9]+

# END QUESTION

# END PUBLIC

# BEGIN GROUP Exam Question One [6]

_This is some very important text_. This text is not so important.

# BEGIN QUESTION [2]

These are some multiple choice questions. You must select exactly one.

# INPUT OPTION Options can be plain text.

# INPUT OPTION Or $\LaTeX$ math,

# INPUT OPTION Or even `code`!

# END QUESTION

# BEGIN QUESTION [4]

This is a short answer question.

# INPUT SHORT_ANSWER

# END QUESTION

# END GROUP

# BEGIN GROUP Another Exam Question [6]

This is another block of questions.

# BEGIN GROUP A subgroup [2]

There can be subgroups of questions.

# BEGIN QUESTION [3]

$\LaTeX$ display math is also supported

$$
    \int_{0}^\infty e^{-x^2 / 2} \, \mathrm{d}x
$$

# INPUT SELECT Select all

# INPUT SELECT options

# INPUT SELECT are also available

# END QUESTION

# END GROUP

# BEGIN QUESTION [7]

You can also include large code blocks in questions

```
m, t = Day(), Week(199)
t.mask(200)(100)(150)(160)
Day.aqi = 140
t.aqi = 160
```

And allow code in answers too

# INPUT LONG_CODE_ANSWER

# END QUESTION

# BEGIN QUESTION

You can omit point values for particular questions, if you want.

Paragraph answers are allowed. You can even specify the number of lines displayed! This block is four lines long.

# INPUT LONG_ANSWER 4

# END QUESTION

# BEGIN QUESTION

Images and other markdown features should all be supported. If it works on GitHub, it should work here.

## Stuff

![](https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 1")

| Tables        |      Are      |   Cool |
| ------------- | :-----------: | -----: |
| col 3 is      | right-aligned | \$1600 |
| col 2 is      |   centered    |   \$12 |
| zebra stripes |   are neat    |    \$1 |

# INPUT SHORT_CODE_ANSWER

# END QUESTION

# END GROUP
