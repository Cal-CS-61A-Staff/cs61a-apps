import { assert } from "./utils.js";

class TokenBuffer {
  /**
   *
   * @param {list} tokens
   */
  constructor(tokens) {
    this.tokens = tokens;
    this.i = 0;
  }

  get empty() {
    return this.i === this.tokens.length;
  }

  /**
   *
   * @return {string}
   */
  getNext() {
    return this.tokens[this.i];
  }

  /**
   *
   * @return {string}
   */
  popNext() {
    const out = this.getNext();
    ++this.i;
    return out;
  }
}

export default function parse(sqlString) {
  const tokenized = tokenize(sqlString);
  if (tokenized[tokenized.length - 1] !== ";") {
    tokenized.push(";");
  }
  return getExpression(new TokenBuffer(tokenized));
}

/**
 *
 * @param {TokenBuffer} buffer
 */
function getExpression(buffer) {
  const helpers = {
    FROM: buildIterator(buildAliased(getName)),
    WHERE: getExpr,
    GROUP: getGroups,
    HAVING: getExpr,
    ORDER: getOrder,
    LIMIT: getLimit,
    DESC: getLimit,
  };
  if (buffer.empty) {
    throw Error("No tokens found");
  }
  const curr = buffer.popNext().toUpperCase();
  if (curr === "SELECT") {
    const out = {};
    out.COLUMNS = buildIterator(buildAliased(getExpr))(buffer);
    for (const specifier of Object.keys(helpers)) {
      const nextToken = buffer.getNext();
      if (nextToken === ";") {
        return out;
      } else if (nextToken.toUpperCase() === specifier) {
        buffer.popNext();
        out[specifier] = helpers[specifier](buffer);
      }
    }
    assert(buffer.popNext() === ";", "SELECT statement not terminated.");
    return out;
  } else if (curr === "CREATE") {
    assert(buffer.popNext().toUpperCase() === "TABLE");
    const tableName = buffer.popNext();
    assert(buffer.popNext().toUpperCase() === "AS");
    return { TABLENAME: tableName, SELECT: getExpression(buffer) };
  } else {
    throw Error("Can only handle SELECT statements right now.");
  }
}

function getGroups(buffer) {
  assert(
    buffer.popNext().toUpperCase() === "BY",
    "GROUP must be followed by BY"
  );
  return buildIterator(getExpr)(buffer);
}

function getName(buffer) {
  return buffer.popNext();
}

function getOrder(buffer) {
  assert(
    buffer.popNext().toUpperCase() === "BY",
    "GROUP must be followed by BY"
  );
  return buildIterator(getExpr)(buffer);
}

function getLimit(buffer) {
  if (buffer.getNext().toUpperCase() === "LIMIT") {
    buffer.popNext();
  }
  return getExpr(buffer);
}

function buildAliased(callback) {
  return (buffer) => {
    const out = { alias: [] };
    out.expr = callback(buffer);
    if (buffer.getNext().toUpperCase() === "AS") {
      buffer.popNext();
      out.alias.push(buffer.popNext());
    }
    return out;
  };
}

function buildIterator(callback) {
  return (buffer) => {
    const out = [];
    for (;;) {
      out.push(callback(buffer));
      if (buffer.getNext() !== ",") {
        return out;
      }
      buffer.popNext();
    }
  };
}

function getExpr(buffer) {
  const seq = [];
  const operators = [
    "OR",
    "AND",
    "!",
    "!=",
    "=",
    ">",
    ">=",
    "<",
    "<=",
    "+",
    "-",
    "*",
    "/",
  ];
  for (;;) {
    let val;
    if (buffer.getNext() === "(") {
      // grab parened
      buffer.popNext();
      val = getExpr(buffer);
      assert(buffer.popNext() === ")", "Parens not closed correctly");
    } else if (buffer.getNext() === "-" || buffer.getNext() === "+") {
      // unary minus
      const operator = buffer.popNext();
      val = {
        type: "combination",
        operator,
        left: { type: "atom", val: { type: "numeric", val: "0" } },
        right: getExpr(buffer),
      };
    } else {
      // grab single
      const first = buffer.popNext();
      if (first === '"' || first === '"') {
        val = { type: "string", val: buffer.popNext() };
        assert(buffer.popNext() === first, "Quotation marks must be matched.");
      } else if (buffer.getNext() === ".") {
        buffer.popNext();
        const column = buffer.popNext();
        val = { type: "dotaccess", table: first, column };
      } else if (buffer.getNext() === "(") {
        buffer.popNext();
        const expr = getExpr(buffer);
        assert(
          buffer.popNext() === ")",
          "Aggregates should only take one expression."
        );
        val = { type: "aggregate", operator: first, expr };
      } else if (/^\d+$/.test(first)) {
        val = { type: "numeric", val: first };
      } else {
        val = { type: "column", column: first };
      }
    }
    seq.push(val);
    if (operators.includes(buffer.getNext().toUpperCase())) {
      let operator = buffer.popNext().toUpperCase();
      if (operator === "!") {
        assert(buffer.popNext() === "=", "Unknown operator: !");
        operator = "!=";
      } else if (operator === "<") {
        if (buffer.getNext() === ">") {
          buffer.popNext();
          operator = "!=";
        } else if (buffer.getNext() === "=") {
          buffer.popNext();
          operator = "<=";
        }
      } else if (operator === ">") {
        if (buffer.getNext() === "=") {
          buffer.popNext();
          operator = ">=";
        }
      }
      seq.push(operator);
    } else {
      break;
    }
  }

  // eslint-disable-next-line no-shadow
  function hierarchize(seq) {
    if (seq.length === 1) {
      if (seq[0].type !== "combination") {
        return { type: "atom", val: seq[0] };
      } else {
        return seq[0];
      }
    }
    for (const operator of operators) {
      const index = seq.findIndex((x) => x === operator);
      if (index === -1) {
        continue;
      }
      return {
        type: "combination",
        operator,
        left: hierarchize(seq.slice(0, index)),
        right: hierarchize(seq.slice(index + 1, seq.length)),
      };
    }
    assert(false, "hierarchize failed");
    return false;
  }

  return hierarchize(seq);
}

/**
 * @param {string} sqlString: the string to tokenize
 * @return {list} A list of tokens as strings
 */
function tokenize(sqlString) {
  const SPECIALS = [
    "=",
    "(",
    ")",
    '"',
    "'",
    ".",
    ",",
    "-",
    "+",
    "*",
    "/",
    ";",
    "<",
    ">",
    "!",
  ];

  let i = 0;
  const out = [];

  // should be called with i pointing at a non-space char
  function getToken() {
    let curr = "";
    while (i !== sqlString.length) {
      const nextChar = sqlString[i];
      ++i;
      if (nextChar.trim() === "") {
        return curr;
      } else if (SPECIALS.includes(nextChar)) {
        if (curr) {
          --i;
          return curr;
        } else {
          curr = nextChar;
          if (nextChar === '"') {
            out.push(curr);
            out.push(getString(curr));
            ++i;
          }
          return curr;
        }
      }
      curr += nextChar;
    }
    return curr;
  }

  function getString(close) {
    let curr = "";
    while (i !== sqlString.length && sqlString[i] !== close) {
      curr += sqlString[i];
      ++i;
    }
    return curr;
  }

  while (i !== sqlString.length) {
    if (sqlString[i].trim() === "") {
      ++i;
      continue;
    }
    out.push(getToken());
  }

  return out;
}
