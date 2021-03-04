# Writing Exams

Essentially, you write your exam in Markdown, with some special commands to
separate questions / question groups and to change settings.

An exam is made up of groups, which each contain questions.
Each question can be:

- Short (code?) answer
- Long (code?) answer
- Multiple choice
- Select all

Groups and questions can contain description text written in Markdown, including

- Images
- Tables
- LaTeX
- Code blocks

Basically anything that works in GitHub Markdown should work here - if it doesn't work,
it should be considered a bug.

The general syntax of this structure looks like:

```
# BEGIN GROUP Section 1

# BEGIN QUESTION
This is a question
# INPUT SHORT_ANSWER
# END QUESTION

# BEGIN QUESTION
This is another question, that's multiple-choice.

# INPUT OPTION Option 1
# INPUT OPTION Option 2

# END QUESTION

# END GROUP
```

## Group Syntax

Each group block is introduced with a

```
# BEGIN GROUP <title> [<points>]
```

statement. The title and point values are both optional. For instance,

```
# BEGIN GROUP Gobears [4]
```

creates a group of questions called `Gobears` worth `4` points. Note that a group title
_must_ be in plain text, _not_ Markdown.

Each group then can have some body text written in Markdown. After this body text comes a
sequence of element blocks. Element blocks are either nested group blocks or question blocks. Then a group is ended with

```
# END GROUP
```

Groups can also contain config statements. If you include the config statement

```
# CONFIG PICK <num>
```

within a group block, then only `num` elements (subgroups or questions) will be randomly selected and presented to the student, rather than the entire group.

If you include the config statement

```
# CONFIG SCRAMBLE
```

within a group block, then its enclosed elements will be randomly re-ordered.

## Question Syntax

Each question block is introduced with

```
# BEGIN QUESTION [<points>]
```

Note that, unlike groups, questions do not have titles. Then you can provide some question
body text, written in Markdown. Then you must provide at least one `INPUT` statement. Then
you can provide `SOLUTION` and `NOTE` blocks. 

Additionally, you can set a constant ID for your question by setting the config ID such as

```
# CONFIG ID MYNEWID
```

Then a question is ended with

```
# END QUESTION
```

## Input Syntax

An input statement is written as

```
# INPUT <type> <content>
```

All the input statements within a single question must be of the same `type`.

For multiple-choice questions, you put one input statement for each possible choice,
with `type = OPTION` for select-one, and `type = SELECT` for select-all. The value of the choice
is the `content`, written in Markdown. For instance, you could write

```
# INPUT OPTION An option
```

to provide a single multiple choice option with value `An option`.

To fix an option in place even if `SCRAMBLE_OPTIONS` is enabled, use the syntax

```
# INPUT <type> FIXED <content>
```

and it will not be shuffled.

To indicate a correct option when generating solutions, use the syntax

```
# INPUT <type> CORRECT <content>
```

If `FIXED` and `CORRECT` are used together, use the syntax

```
# INPUT <type> FIXED CORRECT <content>
```

Note that the order matters. Exact duplicate options cannot be used in a single question.

To enter `<content>` that spans multiple lines, use a backslash `\` to indicate that the content continues
on the next line. For instance
```
# INPUT <type> FIXED CORRECT <first_content> \
<more_content> \
<even_more_content>
```
This syntax can be used anywhere to include newlines in a single-line element.

For short / long answer questions, you must provide exactly one input statement within that question.
The `type` can be `SHORT_ANSWER`, `SHORT_CODE_ANSWER`, `LONG_ANSWER`, or `LONG_CODE_ANSWER`. `CODE`
means that the font will be monospaced and tab will work to indent text typed in a `LONG_CODE_ANSWER`.
For short answer questions, the `content` should be left blank. For long answer questions, the `content`
can optionally be an integer representing the number of lines provided in the input field before the user
has to start scrolling. This also affects the height of the box in the generated PDF in a similar way.

## Solution and Note Syntax

Each solution block looks like

```
# BEGIN SOLUTION
...
# END SOLUTION
```

and each note block looks like

```
# BEGIN NOTE
...
# END NOTE
```

Solutions will be included in the text entry box in the PDF when solutions are generated, and notes will be
included _after_ the text entry box (e.g. as further explanations). Notes can be included for any type of
question, but solutions can only be included for free-response type questions.

## Public Syntax

If you want to have some questions that can be filled out before the exam starts, use a

```
# BEGIN PUBLIC
...
# END PUBLIC
```

block, just like a group block. This will create a question group that is visible before students start the
exam. At most one such block can exist in the exam.

## Config Syntax

At the beginning of the exam, before anything else, you can provide config statements, written as

```
# CONFIG <option>
```

The valid choices of `option` are `SCRAMBLE_GROUPS` and `SCRAMBLE_OPTIONS`. These will
randomize the order of groups and questions or multiple choice options respectively for each student. The tool
will de-randomize all of these before grading.

To randomize just groups at a particular depth, write

```
# CONFIG SCRAMBLE_GROUPS <depth> <depth> ...
```

to specify the scrambled depths, which are zero-indexed. Questions are one level lower than their parent group.

To fix a particular group or question in its place while scrambling the others, use the syntax
`# BEGIN GROUP FIXED` or `# BEGIN QUESTION FIXED`. You can still provide titles (for groups) and point values
while using this syntax.

## Define Syntax

It is also possible to replace particular words or variables in an exam for each student, to prevent cheating.
The syntax is

```
# DEFINE <target> <alt1> <alt2> ...
```

This will replace all instances of `target` with one of the alternatives, chosen randomly. This will be scoped to
the block where it is made i.e. if it is written at the top-level, it will replace the `target` everywhere in the document,
if it is written in a group, it will replace the `target` everywhere in the group, etc.

If you have a set of variables which should be replaced with a set of another, and you do not want duplicate choices, you can use this define syntax:

```
# DEFINE MATCH [<target1> <target2> ...] [<alt1> <alt2> ...]
```

This will uniquely set each target with one of the alts. You may have more alts than targets but you **must** have at least as many alts as targets.

If you have a group of variables that should be replaced with one of a list of alternative groups, you can use the define statement
```
# DEFINE GROUP (<target1> <target2> ...) (<alt1a> <alt2a> ...) (<alt1b> <alt1b>... ) ...
```
It will either set `target1` to `alt1a` and `target2` to `alt2a`, or `target1` to `alt1b` and `target2` to `alt2b`.

Note that this syntax does not support Markdown - it is a very naive text substitution in the generated HTML, so don't
try anything too fancy with it!

## Inline Groups
To allow for more advanced scrambling, you can use the config statement
```
# CONFIG INLINE
```
within a group to move its child elements into its parent. This is useful when using `# CONFIG PICK`.

As an example, consider the following exam pseudo-structure
```
# BEGIN GROUP
    # BEGIN GROUP 1
        # Q 1A
        # Q 1B
        # Q 1C
        # CONFIG PICK 2
        # CONFIG INLINE
    # END GROUP
    # BEGIN GROUP 2
        # Q 2A
        # Q 2B
        # Q 2C
        # CONFIG PICK 2
        # CONFIG INLINE
    # END GROUP
    # CONFIG PICK 3
    # CONFIG SHUFFLE
# END GROUP
```

The tool will pick two questions from group 1 and two from group 2. Then these four questions will be placed in
the enclosing group, replacing their nested groups. Then, out of these four questions, three will be chosen.

Thus, we obtain a single group with three questions in random order, at most two of which can be
from category 1 or category 2.

## Import Syntax

To write exams over multiple files, use the syntax
```
# IMPORT <path>
```
to insert the contents of the file at `<path>` in the current file. The `<path>` is evaluated with respect to the
folder containing the importing file, and may be a relative or absolute path.
