import React from "react";
import Editor from "./Editor";
import Graphics from "./Graphics";
import OKResults from "./OKResults";
import Output from "./Output";
import { send, sendNoInteract } from "../utils/communication.js";
import {
  SAVE_FILE,
  SHOW_ERROR_DIALOG,
  SHOW_SAVE_DIALOG,
  SHOW_SHARE_DIALOG,
} from "../../common/communicationEnums.js";
import { LARK, PYTHON, SCHEME, SQL } from "../../common/languages.js";
import {
  Debugger,
  debugPrefix,
  extension,
  format,
  generateDebugTrace,
  runCode,
  runFile,
  testCode,
} from "../utils/dispatch.js";
import { ERROR, INPUT, OUTPUT } from "../../common/outputTypes.js";

const DEBUG_MARKER = "DEBUG: ";
const EDITOR_MARKER = "EDITOR: ";
const EXEC_MARKER = "EXEC: ";
export const DOCTEST_MARKER = "DOCTEST: ";
const TURTLE_MARKER = "TURTLE: ";

export default class File extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      name: this.props.initFile.name,
      editorText: this.props.initFile.content,
      savedText: this.props.initFile.location
        ? this.props.initFile.content
        : -1,
      location: this.props.initFile.location,

      shareRef: this.props.initFile.shareRef || null,

      outputData: [],
      outputActive: false,

      graphicsData: [],

      executedCode: [],

      debugData: null,
      editorInDebugMode: false,
      editorDebugData: null,

      doctestData: null,

      interactCallback: null,
      killCallback: null,
      detachCallback: null,
    };

    this.isSaving = false;

    this.editorRef = React.createRef();
    this.outputRef = React.createRef();
    this.debugRef = React.createRef();
    this.testRef = React.createRef();
    this.graphicsRef = React.createRef();

    this.props.onActivate(this.props.id);
  }

  componentDidMount() {
    if (this.props.startInterpreter) {
      this.run();
    } else {
      this.editorRef.current.forceOpen();
    }
    if (this.props.srcOrigin) {
      window.addEventListener("message", (e) => {
        if (e.origin === this.props.srcOrigin && typeof e.data === "string") {
          this.handleEditorChange(e.data);
        }
      });
      window.parent.postMessage({ requestData: true }, this.props.srcOrigin);
    }
  }

  componentWillUnmount() {
    if (this.state.killCallback) {
      this.state.detachCallback();
      this.state.killCallback();
    }
  }

  run = async () => {
    if (this.state.location) {
      await this.save();
    }
    if (this.state.killCallback) {
      this.state.detachCallback();
      this.state.killCallback();
    }
    let interactCallback;
    let killCallback;
    let detachCallback;

    const numTrunc = this.state.outputData.length;

    this.setState((state) => {
      state.graphicsData.push(["clear"]);

      return {
        // eslint-disable-next-line react/no-access-state-in-setstate
        executedCode: [],
        interactCallback,
        killCallback,
        detachCallback,
        outputData: state.outputData.slice(numTrunc),
        outputActive: true,
      };
    });

    this.outputRef.current.forceOpen();

    if (ELECTRON && this.state.location) {
      [interactCallback, killCallback, detachCallback] = runFile(
        this.identifyLanguage()
      )(
        this.state.location,
        (out) => this.handleOutputUpdate(out, false),
        (out) => this.handleOutputUpdate(out, true),
        this.handleHalt
      );
    } else {
      [interactCallback, killCallback, detachCallback] = runCode(
        this.identifyLanguage()
      )(
        this.state.editorText,
        (out) => this.handleOutputUpdate(out, false),
        (out) => this.handleOutputUpdate(out, true),
        this.handleHalt
      );
    }
  };

  test = async () => {
    if (this.state.location) {
      await this.save();
    }

    const duration = this.props.settings.doctestTimeout;
    const timeoutTimer = setTimeout(() => {
      send({
        type: SHOW_ERROR_DIALOG,
        title: "Doctests Failed",
        message: `Timeout (tests did not complete after ${duration}s). You might have an infinite loop!`,
      });
      // eslint-disable-next-line no-use-before-define
      kill();
    }, duration * 1000);

    const kill = testCode(this.identifyLanguage())(
      this.state.editorText,
      (doctestData) => {
        this.setState({ doctestData });
        this.testRef.current.forceOpen();
        clearInterval(timeoutTimer);
      },
      (message) => {
        clearInterval(timeoutTimer);
        send({
          type: SHOW_ERROR_DIALOG,
          title: "Doctests Failed",
          message,
        });
      }
    );
  };

  debugTest = (data) => {
    this.debugExecutedCode(
      null,
      `${this.state.editorText}\n${data.code.join("\n")}`
    );
  };

  debug = (data) => {
    this.debugExecutedCode(data, this.state.editorText);
  };

  debugExecutedCode = async (existingDebugData, editorCode) => {
    const TEMPLATE_CODE = debugPrefix(this.identifyLanguage());
    const code =
      TEMPLATE_CODE + (editorCode || this.state.executedCode.join("\n"));
    const debugData =
      existingDebugData ||
      (await generateDebugTrace(this.identifyLanguage())(code));
    if (debugData.success) {
      this.setState({ debugData: debugData.data, editorInDebugMode: true });
      this.editorRef.current.forceOpen();
      this.debugRef.current.forceOpen();
    } else {
      send({
        type: SHOW_ERROR_DIALOG,
        title: "Unable to debug",
        message: debugData.error,
      });
    }
  };

  format = async () => {
    // eslint-disable-next-line react/no-access-state-in-setstate
    const ret = await format(this.identifyLanguage())(this.state.editorText);
    if (ret.success) {
      this.setState({ editorText: ret.code });
    } else {
      send({
        type: SHOW_ERROR_DIALOG,
        title: "Unable to format",
        message: ret.error,
      });
    }
  };

  save = async () => {
    if (this.isSaving) {
      return;
    }
    this.isSaving = true;
    if (!this.state.location) {
      await this.saveAs();
    } else {
      const savedText = this.state.editorText;
      const ret = await sendNoInteract({
        type: SAVE_FILE,
        contents: savedText,
        location: this.state.location,
        shareRef: this.state.shareRef,
      });
      if (ret.success) {
        this.setState({ savedText });
      } else if (!ret.hideError) {
        send({
          type: SHOW_ERROR_DIALOG,
          title: "Unable to save",
          message: ret.message,
        });
      }
    }
    this.isSaving = false;
  };

  saveAs = async () => {
    const savedText = this.state.editorText;
    const hint = this.state.name.includes(".")
      ? this.state.name
      : (this.state.name += extension(this.identifyLanguage()));
    const ret = await sendNoInteract({
      type: SHOW_SAVE_DIALOG,
      contents: savedText,
      shareRef: this.state.shareRef,
      hint,
    });
    if (ret.success) {
      this.setState({
        name: ret.name,
        savedText,
        location: ret.location,
      });
    } else if (!ret.hideError) {
      send({
        type: SHOW_ERROR_DIALOG,
        title: "Unable to save",
        message: ret.message,
      });
    }
  };

  share = async () => {
    const savedText = this.state.editorText;
    const ret = await sendNoInteract({
      type: SHOW_SHARE_DIALOG,
      contents: savedText,
      name: this.state.name,
      shareRef: this.state.shareRef,
    });
    if (ret.success) {
      this.setState({ shareRef: ret.shareRef });
    }
  };

  handleDebugUpdate = (editorDebugData) => {
    this.setState({ editorDebugData });
  };

  handleOutputUpdate = (text, isErr) => {
    if (text.startsWith(DEBUG_MARKER)) {
      this.debugExecutedCode();
    } else if (text.startsWith(EDITOR_MARKER)) {
      this.editorRef.current.forceOpen();
      if (!this.state.editorText) {
        this.setState((state) => ({
          editorText: state.executedCode.join("\n"),
        }));
      }
    } else if (text.startsWith(EXEC_MARKER)) {
      const code = text.substr(EXEC_MARKER.length);
      this.setState((state) => ({
        executedCode: state.executedCode.concat([code]),
      }));
    } else if (text.startsWith(TURTLE_MARKER)) {
      // eslint-disable-next-line no-eval
      const data = (0, eval)(`(${text.substr(DEBUG_MARKER.length)})`);
      this.setState(({ graphicsData }) => {
        graphicsData.push(data);
        return { graphicsData };
      });
      this.graphicsRef.current.forceOpen();
    } else {
      this.setState((state) => {
        const outputData = state.outputData.concat([
          {
            text,
            type: isErr ? ERROR : OUTPUT,
          },
        ]);
        return { outputData };
      });
    }
  };

  handleHalt = (text) => {
    this.handleOutputUpdate(text, true);
    this.setState({ outputActive: false });
  };

  handleStop = () => {
    this.state.killCallback();
  };

  handleActivate = () => {
    this.props.onActivate(this.props.id);
  };

  handleInput = (line) => {
    this.setState((state) => {
      const outputData = state.outputData.concat([
        {
          text: line,
          type: INPUT,
        },
      ]);
      return { outputData };
    });
    this.state.interactCallback(line);
  };

  handleEditorChange = (editorText) => {
    if (this.props.srcOrigin) {
      /*
      It is not possible to exfiltrate data, since srcOrigin is only set when the caller
      *also* is supplying the _contents_ of the file, so there's no data to steal!
       */
      window.parent.postMessage(
        { fileName: this.props.initFile.name, data: editorText },
        this.props.srcOrigin
      );
    }
    this.setState((state) => ({
      editorText,
      editorInDebugMode:
        state.editorDebugData && state.editorDebugData.code === editorText,
    }));
    this.handleActivate();
  };

  identifyLanguage = () => {
    const name = this.state.name.toLowerCase();

    const candidates = [PYTHON, SCHEME, SQL, LARK];

    for (const lang of candidates) {
      if (name.endsWith(extension(lang))) {
        return lang;
      }
    }

    const code = this.state.editorText.toLowerCase();
    if (code.split("def ").length > 1) {
      return PYTHON;
    } else if (code.split("select").length > 1) {
      return SQL;
    } else if (code.trim()[0] === "(" || code.split(";").length > 1) {
      return SCHEME;
    } else if (
      code.split(": ").length > 1 ||
      code.split("%ignore").length > 1
    ) {
      return LARK;
    } else {
      return PYTHON;
    }
  };

  render() {
    const title =
      this.state.name +
      (this.state.editorText === this.state.savedText ? "" : "*");
    const editorDebugData = this.state.editorInDebugMode
      ? this.state.editorDebugData
      : null;
    const language = this.identifyLanguage();

    const CurrDebugger = Debugger(language);

    return (
      <>
        <Editor
          ref={this.editorRef}
          text={this.state.editorText}
          language={language}
          title={title}
          onActivate={this.handleActivate}
          onChange={this.handleEditorChange}
          debugData={editorDebugData}
          shareRef={this.state.shareRef}
          enableAutocomplete={this.props.settings.enableAutocomplete}
        />
        <Output
          ref={this.outputRef}
          title={`${this.state.name} (Output)`}
          data={this.state.outputData}
          lang={language}
          outputActive={this.state.outputActive}
          onStop={this.handleStop}
          onRestart={this.run}
          onInput={this.handleInput}
        />
        {CurrDebugger && (
          <CurrDebugger
            ref={this.debugRef}
            title={`${this.state.name} (Debug)`}
            data={this.state.debugData}
            onUpdate={this.handleDebugUpdate}
          />
        )}
        <OKResults
          ref={this.testRef}
          title={`${this.state.name} (Tests)`}
          onDebug={this.debugTest}
          data={this.state.doctestData}
        />
        <Graphics
          ref={this.graphicsRef}
          title={`${this.state.name} (Graphics)`}
          data={this.state.graphicsData}
        />
      </>
    );
  }
}

// File.propTypes = {
//     id: PropTypes.object,
//     initFile: PropTypes.shape({
//         name: PropTypes.string,
//         content: PropTypes.string,
//         location: PropTypes.object,
//     }),
//     onActivate: PropTypes.func,
// };
