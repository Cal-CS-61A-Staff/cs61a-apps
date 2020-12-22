class Flag {
  constructor(shortForm, longForm, name, explanation) {
    this.shortForm = shortForm;
    this.longForm = longForm;
    this.name = name;
    this.explanation = explanation;
    this.isValue = false;
  }
}

class Value {
  constructor(shortForm, longForm, name, explanation) {
    this.shortForm = shortForm;
    this.longForm = longForm;
    this.name = name;
    this.explanation = explanation;
    this.isValue = true;
  }
}

class Category {
  constructor(name, explanation, mandatoryArgs, optionalArgs) {
    this.name = name;
    this.explanation = explanation;
    this.mandatoryArgs = mandatoryArgs;
    this.optionalArgs = optionalArgs;
  }
}

const QUESTION_VALUE = new Value(
  "q",
  "question",
  "Select Question",
  "Choose which question you want to work on. If you don't set this " +
    "option, okpy will go through all the questions!"
);

const VERBOSE_FLAG = new Flag(
  "v",
  "verbose",
  "Verbose",
  "Show the results of all tests, not just those that fail."
);

const ALL_FLAG = new Flag(
  null,
  "all",
  "All",
  "Run tests for all the questions in the config file, including optional questions."
);

const SUBMIT_FLAG = new Flag(
  null,
  "submit",
  "Submit",
  "Submit your progress so far on all questions in the assignment."
);

const REVISE_FLAG = new Flag(
  null,
  "revise",
  "Revise",
  "Submit your composition revisions for the assignment."
);

const BACKUP_FLAG = new Flag(
  null,
  "backup",
  "Backup",
  "Backup your progress so far on all questions in the assignment, without submitting."
);

const LOCAL_FLAG = new Flag(
  null,
  "local",
  "Local",
  "Run locally, without backing up to or downloading updates from the server."
);

const INTERACTIVE_FLAG = new Flag(
  "i",
  "interactive",
  "Interactive Mode",
  "Start the Python interpreter after a failed test, to help debug."
);

const VERSION_FLAG = new Flag(
  null,
  "version",
  "Version",
  "Print the current version of okpy and then exit."
);

const HELP_FLAG = new Flag(
  "h",
  "help",
  "Help",
  "Print the help message built into okpy and then exit."
);

const TESTS_FLAG = new Flag(
  null,
  "tests",
  "View Tests",
  "View all the test names available in the current assignment."
);

const AUTHENTICATE_FLAG = new Flag(
  null,
  "authenticate",
  "Authenticate",
  "Re-authenticate with okpy, even if you are already signed in."
);

const NO_BROWSER_FLAG = new Flag(
  null,
  "no-browser",
  "No Browser",
  "Do not use a web browser for authentication."
);

const UPDATE_FLAG = new Flag(
  null,
  "update",
  "Update",
  "Update okpy, if an update is available, and then exit."
);

const SCORE_FLAG = new Flag(
  null,
  "score",
  "Score",
  "Score all questions based on number of tests passed for each."
);

export default [
  new Category(
    "Unlock",
    "You should unlock the test cases for each problem before solving it.",
    [new Flag("u", "unlock", "Unlock")],
    [QUESTION_VALUE, LOCAL_FLAG, NO_BROWSER_FLAG]
  ),
  new Category(
    "Run Tests",
    "After writing code, you should test it against the provided test cases.",
    [],
    [
      QUESTION_VALUE,
      INTERACTIVE_FLAG,
      VERBOSE_FLAG,
      SCORE_FLAG,
      ALL_FLAG,
      LOCAL_FLAG,
      NO_BROWSER_FLAG,
    ]
  ),
  new Category(
    "Submission",
    "When you're ready, you can submit your code for us to grade.",
    [],
    [SUBMIT_FLAG, REVISE_FLAG, BACKUP_FLAG, NO_BROWSER_FLAG]
  ),
  new Category(
    "Advanced",
    "Okpy is a powerful tool - try out some of the more advanced options!",
    [],
    [
      AUTHENTICATE_FLAG,
      TESTS_FLAG,
      VERSION_FLAG,
      NO_BROWSER_FLAG,
      UPDATE_FLAG,
      HELP_FLAG,
    ]
  ),
];
