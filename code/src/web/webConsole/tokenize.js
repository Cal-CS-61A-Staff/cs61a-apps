/* eslint-disable no-param-reassign */
export default function splitCommand(raw) {
  let pos = 0;
  const args = [];
  while (pos !== raw.length) {
    let token;
    [pos, token] = getToken(raw, pos);
    if (token !== null) {
      args.push(token);
    }
  }
  return args;
}

function isWhitespace(char) {
  return /\s/.test(char);
}

function getToken(raw, pos) {
  while (pos !== raw.length && isWhitespace(raw[pos])) {
    ++pos;
  }
  if (pos === raw.length) {
    return [pos, null];
  }
  if (raw[pos] === '"') {
    return getRestOfString(raw, pos + 1);
  } else {
    const out = [];
    while (pos !== raw.length && !isWhitespace(raw[pos])) {
      out.push(raw[pos]);
      ++pos;
    }
    return [pos, out.join("")];
  }
}

function getRestOfString(raw, pos) {
  const out = [];
  while (pos !== raw.length) {
    if (raw[pos] === '"') {
      ++pos;
      return [pos, `"${out.join("")}"`];
    } else if (raw[pos] === "\\") {
      ++pos;
      if (pos === raw.length) {
        throw Error("Unexpected backslash");
      }
      const escaped = raw[pos];
      switch (escaped) {
        case "'":
          out.push("'");
          break;
        case '"':
          out.push('"');
          break;
        case "\\":
          out.push("\\");
          break;
        case "\n":
          out.push("\n");
          break;
        case "\r":
          out.push("\r");
          break;
        case "\b":
          out.push("\b");
          break;
        case "\f":
          out.push("\f");
          break;
        case "\v":
          out.push("\v");
          break;
        case "\0":
          out.push("\0");
          break;
        default:
          out.push(escaped);
      }
    } else {
      out.push(raw[pos]);
    }
    ++pos;
  }
  throw Error("String not terminated.");
}
