import {
  assert,
  placeHorizontally,
  tableFormat,
  generateHslaColors,
} from "./utils.js";
import parse from "./parser.js";

export default function visualize(sql, db) {
  const parsed = parse(sql);

  if (parsed.TABLENAME) {
    const out = select(parsed.SELECT, db);
    out.push(tableFormat(db.exec(`SELECT * FROM ${parsed.TABLENAME};`)[0]));
    return out;
  } else {
    const out = select(parsed, db);
    out.push(tableFormat(db.exec(sql)[0]));
    return out;
  }
}

function select(parsedSQL, db) {
  const tables = new Map();
  for (const table of parsedSQL.FROM) {
    const tableName = table.expr;
    tables.set(tableName, db.exec(`SELECT * FROM ${tableName};`)[0]); // what's sql injection anyway
  }
  const out = [];
  let workingTable = join(parsedSQL.FROM, tables, out);
  if (parsedSQL.WHERE) {
    workingTable = where(workingTable, parsedSQL.WHERE, parsedSQL.COLUMNS, out);
  }
  // eslint-disable-next-line no-unused-vars
  let groups;
  if (parsedSQL.GROUP) {
    groups = group(workingTable, parsedSQL.GROUP, parsedSQL.COLUMNS, out);
    if (parsedSQL.HAVING) {
      groups = having(groups, parsedSQL.HAVING, parsedSQL.COLUMNS, out);
    }
  } else {
    groups = [workingTable];
  }

  return out;
}

/**
 *
 * @param {list} tableNames
 * @param {Map} tableData
 * @param out
 */
function join(tableNames, tableData, out) {
  const tables = [];
  for (const tableName of tableNames) {
    const cols = [];
    const realName = tableName.expr;
    let displayName;
    if (tableName.alias.length > 0) {
      [displayName] = tableName.alias;
    } else {
      displayName = tableName.expr;
    }
    for (const column of tableData.get(realName).columns) {
      cols.push(`${displayName}.${column}`);
    }
    const tableToJoin = {
      columns: cols,
      values: tableData.get(realName).values,
    };
    tables.push(tableToJoin);
  }

  let defaultColorCallback;
  if (tableNames.length === 1) {
    defaultColorCallback = () => "transparent";
  }

  const tableDivs = [];
  for (const table of tables) {
    let colorCallback;
    if (defaultColorCallback) {
      colorCallback = defaultColorCallback;
    } else {
      colorCallback = alternatingColorCallback(1, table.values.length);
    }
    tableDivs.push(tableFormat(table, colorCallback));
  }
  out.push(placeHorizontally(tableDivs)); // just getting the tables

  if (tableNames.length > 1) {
    // need to visualize a join
    let finalSize = 1;
    for (const table of tables) {
      finalSize *= table.values.length;
    }

    const duplicatedTables = [];
    const duplicatedTableDivs = [];
    let duplicates = finalSize;
    for (const table of tables) {
      duplicates /= table.values.length;
      const repeats = finalSize / duplicates / table.values.length;
      const duplicatedTable = {
        columns: table.columns,
        values: copyRows(table.values, duplicates, repeats),
      };
      duplicatedTables.push(duplicatedTable);
      duplicatedTableDivs.push(
        tableFormat(
          duplicatedTable,
          alternatingColorCallback(duplicates, table.values.length)
        )
      );
    }

    out.push(placeHorizontally(duplicatedTableDivs)); // expanding to visualize the join

    const joinedCols = [];
    for (const table of duplicatedTables) {
      joinedCols.push(...table.columns);
    }
    const joinedVals = [];
    for (let i = 0; i !== finalSize; ++i) {
      const currRow = [];
      for (const table of duplicatedTables) {
        currRow.push(...table.values[i]);
      }
      joinedVals.push(currRow);
    }

    const joinedTable = { columns: joinedCols, values: joinedVals };

    out.push(tableFormat(joinedTable));

    return joinedTable;
  } else {
    return tables[0];
  }
}

function alternatingColorCallback(groupSize, numGroups) {
  const colors = generateHslaColors(20, 80, 1.0, numGroups);
  return (i) => colors[Math.floor(i / groupSize) % numGroups];
}

function copyRows(rows, duplicates, repeats) {
  const out = [];
  for (let i = 0; i !== repeats; ++i) {
    for (const row of rows) {
      for (let j = 0; j !== duplicates; ++j) {
        out.push(row);
      }
    }
  }
  return out;
}

function where(table, whereClause, selectClause, out) {
  const selectedRows = [];
  for (let i = 0; i !== table.values.length; ++i) {
    if (evaluate(whereClause, table.columns, table.values[i], selectClause)) {
      selectedRows.push(i);
    }
  }
  const highlightRows = (i) =>
    selectedRows.includes(i) ? "lightgreen" : "white";
  out.push(tableFormat(table, highlightRows));

  const rows = [];
  for (const row of table.values) {
    if (evaluate(whereClause, table.columns, row, selectClause)) {
      rows.push(row);
    }
  }

  const filteredTable = { columns: table.columns, values: rows };
  out.push(tableFormat(filteredTable));
  return filteredTable;
}

function group(table, groupColumns, selectClause, out) {
  const groups = new Map();
  const groupLookup = [];
  const SPACING = "-------";
  for (let i = 0; i !== table.values.length; ++i) {
    let groupKey = "";
    for (const column of groupColumns) {
      groupKey += evaluate(
        column,
        table.columns,
        table.values[i],
        selectClause
      );
      groupKey += SPACING;
    }
    if (!groups.has(groupKey)) {
      groups.set(groupKey, groups.size);
    }
    groupLookup.push(groups.get(groupKey));
  }

  const colors = generateHslaColors(20, 80, 1.0, groups.size);

  const colorGrouper = (i) => colors[groupLookup[i]];
  out.push(tableFormat(table, colorGrouper));

  const groupedTables = [];
  for (let i = 0; i !== groups.size; ++i) {
    groupedTables.push({ columns: table.columns, values: [] });
  }

  for (let i = 0; i !== groupLookup.length; ++i) {
    groupedTables[groupLookup[i]].values.push(table.values[i]);
  }

  const groupedTableDivs = [];
  for (let i = 0; i !== groups.size; ++i) {
    groupedTableDivs.push(tableFormat(groupedTables[i], () => colors[i]));
  }

  out.push(placeHorizontally(groupedTableDivs));

  return groupedTables;
}

function having(groups, havingClause, selectClause, out) {
  const selectedGroups = new Set();
  for (let i = 0; i !== groups.length; ++i) {
    if (
      evaluate(
        havingClause,
        groups[i].columns,
        groups[i].values[groups[i].values.length - 1],
        selectClause,
        groups[i].values
      )
    ) {
      selectedGroups.add(i);
    }
  }
  const highlightedGroupDivs = [];
  for (let i = 0; i !== groups.length; ++i) {
    let colorCallback;
    if (selectedGroups.has(i)) {
      colorCallback = () => "lightgreen";
    } else {
      colorCallback = () => "white";
    }
    highlightedGroupDivs.push(tableFormat(groups[i], colorCallback));
  }

  out.push(placeHorizontally(highlightedGroupDivs));

  const selectedGroupTables = [];
  for (const selectedGroup of selectedGroups) {
    selectedGroupTables.push(groups[selectedGroup]);
  }

  return selectedGroupTables;
}

function evaluateName(expr, columnNames, rowValues, selectClause) {
  let targetName;
  if (expr.type === "column") {
    targetName = expr.column;
  } else if (expr.type === "dotaccess") {
    targetName = `${expr.table}.${expr.column}`;
  } else {
    assert(false, `Unknown atomic expr type: ${expr.type}`);
  }
  for (let i = 0; i !== columnNames.length; ++i) {
    if (
      columnNames[i] === targetName ||
      columnNames[i].split(".")[1] === targetName
    ) {
      return rowValues[i];
    }
  }
  for (const clause of selectClause) {
    if (clause.alias && clause.alias[0] === targetName) {
      return evaluate(clause.expr, columnNames, rowValues, selectClause);
    }
  }
  return assert(false, `Unable to evaluate column name: ${targetName}`);
}

function evaluate(whereClause, columnNames, rowValues, selectClause, allRows) {
  if (whereClause.type === "atom") {
    const expr = whereClause.val;
    if (expr.type === "aggregate") {
      assert(
        allRows !== undefined,
        "aggregates can't be used in the WHERE clause"
      );
      const func = expr.operator.toLowerCase();
      const argument = expr.expr;
      const vals = [];
      for (const row of allRows) {
        if (argument.type === "atom" && argument.val.column === "*") {
          vals.push(true);
        } else {
          vals.push(
            evaluate(argument, columnNames, row, selectClause, allRows)
          );
        }
      }
      if (func === "max") {
        return Math.max(vals);
      } else if (func === "min") {
        return Math.min(vals);
      } else if (func === "count") {
        return vals.length;
      } else if (func === "sum") {
        return vals.reduce((a, b) => a + b);
      } else {
        assert(false, "unknown aggregate function");
      }
    } else if (expr.type === "numeric") {
      return parseFloat(expr.val);
    } else if (expr.type === "string") {
      return expr.val;
    } else {
      return evaluateName(expr, columnNames, rowValues, selectClause);
    }
  } else if (whereClause.type === "combination") {
    const left = evaluate(
      whereClause.left,
      columnNames,
      rowValues,
      selectClause,
      allRows
    );
    const right = evaluate(
      whereClause.right,
      columnNames,
      rowValues,
      selectClause,
      allRows
    );
    switch (whereClause.operator) {
      case "OR":
        return left || right;
      case "AND":
        return left && right;
      case "!=":
        return left !== right;
      case "=":
        return left === right;
      case ">":
        return left > right;
      case ">=":
        return left >= right;
      case "<":
        return left < right;
      case "<=":
        return left <= right;
      case "+":
        return left + right;
      case "-":
        return left - right;
      case "/":
        return left / right;
      case "*":
        return left * right;
      default:
        assert(false, `Unknown operator: ${whereClause.operator}`);
    }
  } else {
    assert(false, `Unknown clause type: ${whereClause.type}`);
  }
  return false;
}
