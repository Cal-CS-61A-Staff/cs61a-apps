import visualize from "./visualize.js";
import { tableFormat } from "./utils.js";
import { exit, stderr, stdout } from "./sqlWorker.js";

let sql;
let db;

export async function init() {
  sql = await initSqlJs({
    locateFile: (file) => `https://sql.js.org/dist/${file}`,
  });
  db = newDatabase();
}

function newDatabase() {
  return new sql.Database();
}

export default async function execute(command) {
  if (command.startsWith(".")) {
    const split = command.split("\n");
    const rest = split.slice(1).join("\n");
    const dotcommand = split[0];
    if (dotcommand === ".quit" || dotcommand === ".exit") {
      exit("\nSQL web worker terminated.");
      return [];
    } else if (dotcommand === ".editor") {
      stdout("EDITOR: \n");
      return execute(rest);
    } else if (dotcommand === ".tables") {
      const dbRet = db.exec(
        "SELECT name as Tables FROM sqlite_master WHERE type = 'table';"
      );
      if (dbRet.length) {
        return [tableFormat(dbRet[0])].concat(await execute(rest));
      } else {
        return execute(rest);
      }
    } else if (dotcommand === ".schema") {
      const dbRet = db.exec(
        "SELECT (sql || ';') as `CREATE Statements` FROM sqlite_master WHERE type = 'table';"
      );
      if (dbRet.length) {
        return [tableFormat(dbRet[0])].concat(await execute(rest));
      } else {
        return execute(rest);
      }
    } else if (dotcommand === ".open --new") {
      init();
      return execute(rest);
    } else if (dotcommand.startsWith(".open")) {
      stderr(".open is not currently supported, except for the --new flag\n");
      return [];
    } else {
      stderr(`The command ${dotcommand} does not exist.\n`);
      return [];
    }
  }

  let dbRet;
  try {
    dbRet = db.exec(command);
  } catch (err) {
    stderr(`Error: ${err.message}\n`);
    return [];
  }

  if (command.trim()) {
    stdout(`EXEC: ${command}`);
  }
  let visualization;
  try {
    visualization = visualize(command, db);
  } catch (err) {
    console.log(err);
  }

  const out = [];

  for (const table of dbRet) {
    out.push(tableFormat(table));
  }

  if (visualization) {
    return { out, visualization };
  } else {
    return out;
  }
}
