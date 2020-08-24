module.exports = {
  /* your base configuration of choice */
  extends: [
    "airbnb",
    "prettier",
    "prettier/react",
    "plugin:flowtype/recommended",
  ],
  plugins: ["flowtype"],
  parser: "babel-eslint",
  parserOptions: {
    sourceType: "module",
  },
  env: {
    browser: true,
    node: true,
  },
  globals: {
    setSchema: "readonly",
    createAssignments: "readonly",
    COURSE_CODE: "readonly",
  },
  rules: {
    "import/no-unresolved": 0,
    "import/extensions": 0,
    "prefer-const": [
      "error",
      {
        destructuring: "any",
        ignoreReadBeforeAssign: false,
      },
    ],
    "no-use-before-define": [
      2,
      {
        functions: false,
        classes: false,
      },
    ],
    "no-restricted-syntax": [
      "error",
      "ForInStatement",
      "LabeledStatement",
      "WithStatement",
    ],
    "react/jsx-filename-extension": [1, { extensions: [".js", ".jsx"] }],
    "no-else-return": "off",
    "no-nested-ternary": "off",
    "no-plusplus": "off",
    "react/destructuring-assignment": 0,
    "react/require-default-props": 0,
    "react/forbid-prop-types": 0,
    "import/prefer-default-export": 1,
    "react/no-multi-comp": 0,
    "jsx-a11y/click-events-have-key-events": 0,
    "jsx-a11y/no-static-element-interactions": 0,
    "no-continue": 0,
    "react/prop-types": 0,
    "import/no-cycle": 0,
    "no-console": 0,
    "import/no-webpack-loader-syntax": 0,
    "import/no-extraneous-dependencies": ["error", { devDependencies: true }],
    "jsx-a11y/label-has-for": 0,
    "jsx-a11y/control-has-associated-label": 0,
    "jsx-a11y/label-has-associated-control": [
      2,
      {
        assert: "either",
      },
    ],
  },
};
