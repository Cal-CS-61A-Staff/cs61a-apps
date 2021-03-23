import { useState } from "react";
import { exit, out } from "./webBackend.js";

let settingsWatcherKey = null;

const settingsKey = "settings";

const defaultSettings = {
  enableAutocomplete: false,
  doctestTimeout: 5,
};

export function assignSettingsWatcherKey(key) {
  if (settingsWatcherKey) {
    exit(settingsWatcherKey);
  }
  settingsWatcherKey = key;
  out(settingsWatcherKey, JSON.stringify(loadSettings()));
}

export function loadSettings() {
  return {
    ...defaultSettings,
    ...JSON.parse(localStorage.getItem(settingsKey) || "{}"),
  };
}

function saveSettings(settings) {
  try {
    localStorage.setItem(settingsKey, JSON.stringify(settings));
  } catch (e) {
    console.error(e);
  }
}

export function setSettingsKey(key, value) {
  const settings = loadSettings();
  settings[key] = value;
  saveSettings(settings);
  if (settingsWatcherKey) {
    out(settingsWatcherKey, JSON.stringify(settings));
  }
}

export function useSettingsKey(key) {
  const value = loadSettings()[key];
  const [, setSavedValue] = useState(value);
  return [
    value,
    (val) => {
      setSettingsKey(key, val);
      setSavedValue(val);
    },
  ];
}
