const processes = {};
const inputBuffers = new Map();

export function registerProcess(key, process) {
  processes[key] = process;
  if (inputBuffers.has(key)) {
    for (const line of inputBuffers.get(key)) {
      interactProcess(key, line);
    }
    inputBuffers.delete(key);
  }
}

export function getProcess(key) {
  return processes[key];
}

export function interactProcess(key, line) {
  if (getProcess(key)) {
    getProcess(key).stdin.write(line, "utf-8");
  } else {
    if (!inputBuffers.has(key)) {
      inputBuffers.set(key, []);
    }
    inputBuffers.get(key).push(line);
  }
}

export function killProcess(key) {
  const process = getProcess(key);
  if (process == null) {
    console.warn("Unable to kill process", key);
  } else {
    process.kill();
  }
}
