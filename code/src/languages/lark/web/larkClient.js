/* eslint-disable no-await-in-loop */
import $ from "jquery";

import { registerProcess } from "../../../main/processes";
import { exit, out, err } from "../../../web/webBackend";
import { PS1, PS2 } from "../constants/prompts";
import extractLarkTests from "./extractLarkTests";

export default class LarkClient {
  constructor(key) {
    this.key = key;
    this.grammar = null;
    this.cases = null;

    this.inputQueue = [];
    this.blocked = false;
    this.multiline = false;
    this.multilineInput = [];
    this.treeview = true;
    this.stopped = false;
  }

  receive = (code) => {
    const { grammar, cases } = extractLarkTests(code);
    this.grammar = grammar;
    this.cases = cases;
  };

  start = async (code) => {
    registerProcess(this.key, {
      stdin: {
        write: (line) => {
          this.inputQueue.push(line);
          this.run();
        },
      },
      kill: () => {
        this.stop();
        exit(this.key, "\n\nLark client stopped.");
      },
    });

    try {
      this.receive(code);
    } catch (e) {
      console.error(e);
      err(this.key, e.toString());
      exit(this.key, "\n\nLark client stopped.");
      return;
    }

    const { error } = await this.larkRun();
    if (error) {
      err(this.key, error);
      exit(this.key, "\n\nLark client stopped.");
    } else {
      err(this.key, PS1);
    }
  };

  test = async (code) => {
    this.receive(code);
    const { error: grammarError } = await this.larkRun();
    if (grammarError) {
      throw Error(grammarError);
    }
    const results = [];
    for (let i = 0; i !== this.cases.length; ++i) {
      const testCase = this.cases[i];

      const caseName =
        testCase.caseName ||
        (this.cases.length === 1 ? "Doctests" : `Case ${i + 1}`);

      for (const { input, output } of testCase.tests) {
        const lines = input.split("\n");
        const caseCode = [
          PS1 + lines[0],
          ...lines.slice(1).map((line) => PS2 + line),
        ];
        const result = {
          name: [caseName, input],
          rawName: `${caseName} > ${input}`,
          code: [this.grammar, input],
        };
        const { success, error, repr } = await this.larkRun(input);
        if (success) {
          result.success = repr.trim() === output.trim();
          result.raw = (result.success
            ? [...caseCode, output]
            : [...caseCode, "Expected:", output, "Received:", repr]
          ).join("\n");
        } else {
          result.success = false;
          result.raw = [
            ...caseCode,
            "Expected:",
            output,
            "Received:",
            error,
          ].join("\n");
        }
        results.push(result);
      }
    }
    return results;
  };

  stop = () => {
    this.stopped = true;
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
      } else if (line.trim() === ".toggleviz") {
        this.treeview = !this.treeview;
        out(this.key, `Tree view ${this.treeview ? "enabled" : "disabled"}.\n`);
      } else {
        await this.parse(line.slice(0, line.length - 1));
      }

      if (this.multiline) {
        err(this.key, PS2);
      } else {
        err(this.key, PS1);
      }
    }
    this.blocked = false;
  };

  parse = async (text) => {
    const { success, error, parsed, repr } = await this.larkRun(text);
    if (success) {
      if (this.treeview) {
        out(this.key, `DRAW: ${JSON.stringify(["Tree", parsed])}`);
      } else {
        out(this.key, repr);
      }
    } else {
      err(this.key, error);
    }
  };

  larkRun = (text) => {
    if (this.stopped) {
      return { success: false, error: "The process has stopped." };
    }
    return $.post("/api/lark_run", {
      grammar: this.grammar,
      text,
    }).catch((error) => {
      console.error(error);
      return { success: false, error: "An internal error occurred." };
    });
  };
}
