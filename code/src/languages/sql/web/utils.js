export function assert(condition, message) {
  if (!condition) {
    throw Error(message || "Assertion failed");
  }
}

export function tableFormat(raw, colorCallback = () => "transparent") {
  const out = ["<table class='out-table'><thead><tr>"];
  for (const col of raw.columns) {
    out.push(`<th> ${col} </th>`);
  }
  out.push("</tr></thead>");
  for (let i = 0; i !== raw.values.length; ++i) {
    out.push(`<tr style="background-color: ${colorCallback(i)};">`);
    for (const val of raw.values[i]) {
      out.push(`<td> ${val} </td>`);
    }
    out.push("</tr>");
  }
  out.push("</table>");
  return out.join("");
}

export function placeHorizontally(tables) {
  const out = ["<div>"];
  for (const table of tables) {
    out.push('<div style="display: inline-block;">');
    out.push(table);
    out.push("</div> ");
  }
  out.push("</div>");
  return out.join("");
}

// @source https://mika-s.github.io/javascript/colors/hsl/2017/12/05/generating-random-colors-in-javascript.html
export function generateHslaColors(saturation, lightness, alpha, amount) {
  const colors = [];
  const huedelta = Math.trunc(360 / amount);

  for (let i = 0; i < amount; i++) {
    const hue = i * huedelta;
    colors.push(`hsla(${hue},${saturation}%,${lightness}%,${alpha})`);
  }

  return colors;
}
