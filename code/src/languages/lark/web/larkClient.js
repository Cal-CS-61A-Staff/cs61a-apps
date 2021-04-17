/* eslint-disable no-await-in-loop */
import $ from "jquery";

import { registerProcess } from "../../../main/processes";
import { exit, out, err } from "../../../web/webBackend";

export default class LarkClient {
  PS1 = "lark> ";

  PS2 = "....> ";

  constructor(key, grammar) {
    this.key = key;
    this.grammar = grammar;
    this.inputQueue = [];
    this.blocked = false;
    this.multiline = false;
    this.multilineInput = [];
  }

  start = async () => {
    registerProcess(this.key, {
      stdin: {
        write: (line) => {
          this.inputQueue.push(line);
          this.run();
        },
      },
      kill: () => {
        exit(this.key, "\n\nLark client stopped.");
      },
    });
    const { error } = await this.larkRun();
    if (error) {
      err(this.key, error);
      exit(this.key, "\n\nLark client stopped.");
    } else {
      err(this.key, this.PS1);
    }
  };

  run = async () => {
    if (this.blocked) {
      return;
    }
    this.blocked = true;
    while (this.inputQueue.length > 0) {
      const line = this.inputQueue.shift();

      if (this.multiline) {
        if (line.trim() === ".end") {
          await this.parse(this.multilineInput.join(""));
          this.multiline = false;
        } else {
          this.multilineInput.push(line);
        }
      } else if (line.trim() === ".begin") {
        this.multiline = true;
        this.multilineInput = [];
      } else {
        await this.parse(line.slice(0, line.length - 1));
      }

      if (this.multiline) {
        err(this.key, this.PS2);
      } else {
        err(this.key, this.PS1);
      }
    }
    this.blocked = false;
  };

  parse = async (text) => {
    const { success, error, parsed } = await this.larkRun(text);
    if (success) {
      out(this.key, `DRAW: ${JSON.stringify(["Tree", parsed])}`);
    } else {
      err(this.key, error);
    }
  };

  larkRun = (text) =>
    $.post("/api/lark_run", {
      grammar: this.grammar,
      text,
    }).catch((error) => {
      console.error(error);
      return { success: false, error: "An internal error occurred." };
    });
}
