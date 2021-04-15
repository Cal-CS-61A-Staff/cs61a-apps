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
    const { error } = await this.parse();
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
      // eslint-disable-next-line no-await-in-loop
      const { success, error, parsed } = await this.parse(line);
      if (success) {
        out(this.key, `DRAW: ${JSON.stringify(["Tree", parsed])}`);
      } else {
        err(this.key, error);
      }
      err(this.key, this.PS1);
    }
    this.blocked = false;
  };

  parse = (text) =>
    $.post("/api/lark_run", {
      grammar: this.grammar,
      text,
    }).catch((error) => {
      console.error(error);
      return { success: false, error: "An internal error occurred." };
    });
}
