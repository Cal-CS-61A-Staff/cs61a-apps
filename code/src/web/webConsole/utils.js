import path from "path-browserify";

export function checkArgs(func, args, low, high) {
  if (low === high) {
    if (args.length !== low) {
      throw Error(
        `${func} expects ${low} argument${low === 1 ? "" : "s"}, received` +
          ` ${args.length}.`
      );
    }
  } else if (args.length < low || args.length > high) {
    throw Error(
      `${func} expects between ${low} and ${high} arguments, received ${args.length}.`
    );
  }
}

function tildeExpand(inpPath) {
  if (inpPath[0] === "~") {
    return path.join("/home/", inpPath.slice(1));
  } else {
    return inpPath;
  }
}

export function resolveRelativePath(inpPath, workingDirectory) {
  const expanded = path.isAbsolute(tildeExpand(inpPath))
    ? tildeExpand(inpPath)
    : path.join(tildeExpand(workingDirectory), tildeExpand(inpPath));
  if (expanded !== "/" && expanded.endsWith("/")) {
    return expanded.slice(0, -1);
  } else {
    return expanded;
  }
}
