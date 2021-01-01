import { openDB } from "idb";
import path from "path-browserify";
import pathParse from "path-parse";
import post from "../common/post.js";
import { DIRECTORY, FILE } from "../common/fileTypes.js";

const DATABASE = "FileStorage";
const FILE_STORE = "Files";
const VERSION = 2;

async function getDB() {
  const db = await openDB(DATABASE, VERSION, {
    async upgrade(oldDB, oldVersion) {
      if (oldVersion < 1) {
        oldDB.createObjectStore(FILE_STORE, {
          keyPath: "location",
          autoIncrement: true,
        });
      } else if (oldVersion === 1) {
        oldDB.deleteObjectStore(FILE_STORE);
        oldDB.createObjectStore(FILE_STORE, {
          keyPath: "location",
          autoIncrement: true,
        });
      }
      // who needs to preserve files anyway
    },
  });
  await db.put(FILE_STORE, {
    name: "",
    location: "/",
    content: ["/home", "/cs61a"],
    type: DIRECTORY,
    time: 1,
  });
  if (!(await db.get(FILE_STORE, "/home"))) {
    await db.put(FILE_STORE, {
      name: "home",
      location: "/home",
      content: [],
      type: DIRECTORY,
      time: 1,
    });
  }
  return db;
}

export async function storeFile(content, location, type, shareRef = null) {
  return storeFileWorker(await getDB(), content, location, type, shareRef);
}

export async function getFile(location) {
  const db = await getDB();
  return getFileWorker(db, location);
}

async function getFileWorker(db, location) {
  if (isHomePath(location) || location === "/") {
    return db.get(FILE_STORE, normalize(location));
  } else if (isBackupPath(location)) {
    if (location === "/cs61a") {
      const assignments = await getAssignments();
      if (assignments.length === 0) {
        throw Error("Cannot access folder while signed out.");
      }
      return {
        name: "cs61a",
        location,
        content: assignments.map(
          ({ name }) => `/cs61a/${name.split("/").pop()}`
        ),
        type: DIRECTORY,
        time: 1,
      };
    } else {
      // /cs61a/assignment/path
      const assignment = location.split("/")[2];
      try {
        const backups = await getBackups(assignment);
        for (const backup of backups) {
          if (backup.location === location) {
            return backup;
          }
        }
        const content = backups
          .filter(({ location: x }) => x.startsWith(location))
          .map(
            ({ location: x }) =>
              `${location}/${x.slice(location.length).split("/")[1]}`
          );
        return {
          name: assignment,
          location,
          content: [...new Set(content)],
          type: DIRECTORY,
          time: 1,
        };
      } catch {
        return undefined;
      }
    }
  } else {
    return undefined;
  }
}

export async function removeFile(location) {
  if (isHomePath(location)) {
    if (location === "./home") {
      throw Error("Cannot delete directory.");
    }
    const db = await getDB();
    await db.delete(FILE_STORE, location);
    const parDir = normalize(path.dirname(location));
    const enclosingDirectory = await db.get(FILE_STORE, parDir);
    enclosingDirectory.content.splice(
      enclosingDirectory.content.indexOf(location),
      1
    );
    await db.put(FILE_STORE, enclosingDirectory);
  } else {
    throw Error("Cannot delete directory.");
  }
}

export async function getAssignments() {
  try {
    return (
      await post("/api/list_assignments")
    ).data.assignments.filter(({ name }) =>
      ["hw", "lab", "proj", "challenge"].some((x) => name.includes(x))
    );
  } catch {
    return [];
  }
}

export async function getBackups(assignment) {
  const backups = [];
  const {
    data: { backups: ret },
  } = await post("/api/get_backups", { assignment });
  for (const { messages } of ret) {
    for (const { created, contents, kind } of messages) {
      if (kind === "file_contents") {
        for (const [name, content] of Object.entries(contents)) {
          if (name !== "submit") {
            backups.push({
              name: name.split("/").pop(),
              location: `/cs61a/${assignment}/${name}`,
              content,
              type: FILE,
              time: Date.parse(created),
            });
          }
        }
      }
    }
  }
  return backups;
}

export async function getRecentFiles() {
  const db = await getDB();
  const raw = await db.getAll(FILE_STORE);
  return raw.filter((x) => x.type === FILE).sort((a, b) => b.time - a.time);
}

export function normalize(location) {
  const parsed = pathParse(path.normalize(location));
  return path.format(parsed);
}

export async function fileExists(location) {
  return fileExistsWorker(await getDB(), location);
}

async function fileExistsWorker(db, location) {
  return (await getFileWorker(db, location)) !== undefined;
}

async function addToDirectory(db, location, dirname) {
  const directory = await db.get(FILE_STORE, dirname);
  if (directory.type !== DIRECTORY) {
    throw Error("Path does not point to directory.");
  }
  if (!directory.content.includes(location)) {
    directory.content.push(location);
  }
  await db.put(FILE_STORE, directory);
}

async function storeFileWorker(db, content, location, type, shareRef = null) {
  if (isHomePath(location)) {
    if (location === "/home") {
      throw Error("Cannot modify home directory.");
    }
    if (!(await fileExistsWorker(db, path.dirname(location)))) {
      await storeFileWorker(db, [], path.dirname(location), DIRECTORY);
    }
    await addToDirectory(db, location, path.dirname(location));
    await db.put(FILE_STORE, {
      name: path.basename(location),
      location,
      content,
      type,
      shareRef,
      time: new Date().getTime(),
    });
  } else if (isBackupPath(location)) {
    if (type !== FILE) {
      throw Error("Unable to create directory in this location.");
    }
    const [assignment, file] = await backupSplit(location);
    const resp = await post("/api/save_backup", { file, content, assignment });
    if (!resp.success) {
      throw Error("Error when backing up.");
    }
  } else {
    throw Error("Unable to write to directory.");
  }
}

function isHomePath(location) {
  return location.startsWith("/home");
}

function isBackupPath(location) {
  return location.startsWith("/cs61a");
}

async function backupSplit(location) {
  const assignment = location.split("/")[2];
  const prefix = `/cs61a/${assignment}/`;
  const file = location.slice(prefix.length);
  const assignments = await getAssignments();
  if (!assignments.some(({ name }) => name.split("/").pop() === assignment)) {
    throw Error("Assignment not found.");
  }
  return [assignment, file];
}
