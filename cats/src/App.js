import React, { Component } from "react";
import "./App.css";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.min.js";
import Button from "react-bootstrap/Button.js";
import Cookies from "js-cookie";
import FastestWordsDisplay from "./FastestWordsDisplay";
import Input from "./Input.js";
import Indicators from "./Indicators.js";
import Leaderboard from "./Leaderboard.js";
import LoadingDialog from "./LoadingDialog.js";
import Options from "./Options.js";
import OpeningDialog from "./OpeningDialog.js";
import post from "./post";
import Prompt from "./Prompt.js";
import ProgressBars from "./ProgressBars.js";
import HighScorePrompt from "./HighScorePrompt.js";
import TopicPicker from "./TopicPicker";
import { getCurrTime, randomString } from "./utils";

export const Mode = {
  SINGLE: "single",
  MULTI: "multi",
  WELCOME: "welcome",
  WAITING: "waiting",
};

class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      promptedWords: ["Please wait - loading!"],
      typedWords: [],
      wpm: null,
      accuracy: null,
      startTime: 0,
      currTime: 0,
      pigLatin: false,
      autoCorrect: false,
      currWord: "",
      inputActive: false,
      numPlayers: 1,
      mode: Mode.SINGLE,
      playerList: [],
      progress: [],
      showLeaderboard: false,
      fastestWords: [],
      showUsernameEntry: false,
      needVerify: false,
      topics: [],
    };
    this.timer = null;
    this.multiplayerTimer = null;

    post("/request_id").then((id) => {
      if (id !== null) {
        this.setState({ id: id.toString(), mode: Mode.WELCOME });
      }
    });

    if (!Cookies.get("user")) {
      Cookies.set("user", randomString(32));
    }
  }

  componentDidMount() {
    this.initialize();
  }

  componentDidUpdate() {
    if (
      this.state.mode === Mode.WELCOME ||
      this.state.mode === Mode.WAITING ||
      this.state.showLeaderboard
    ) {
      document.getElementById("app-root").style.filter = "blur(5px)";
    } else {
      document.getElementById("app-root").style.filter = "none";
    }
  }

  componentWillUnmount() {
    clearInterval(this.timer);
    clearInterval(this.multiplayerTimer);
  }

  initialize = () => {
    this.setState({
      typedWords: [],
      currWord: "",
      inputActive: true,
      wpm: null,
      accuracy: null,
      fastestWords: [],
    });

    post("/request_paragraph", { topics: this.state.topics }).then((data) => {
      if (this.state.pigLatin) {
        post("/translate_to_pig_latin", {
          text: data,
        }).then((translated) => {
          this.setState({
            promptedWords: translated.split(" "),
          });
        });
      } else {
        this.setState({
          promptedWords: data.split(" "),
        });
      }
    });

    this.setState({ startTime: 0, currTime: 0 });

    clearInterval(this.timer);
    this.timer = null;
  };

  restart = () => {
    this.timer = setInterval(this.updateReadouts, 100);
    this.setState({
      startTime: getCurrTime(),
      currTime: getCurrTime(),
    });
  };

  updateReadouts = async () => {
    const promptedText = this.state.promptedWords.join(" ");
    const typedText = this.state.typedWords.join(" ");
    const { wpm, accuracy } = await post("/analyze", {
      promptedText,
      typedText,
      startTime: this.state.startTime,
      endTime: getCurrTime(),
    });
    this.setState({ wpm, accuracy, currTime: getCurrTime() });
    return { wpm, accuracy };
  };

  reportProgress = () => {
    const promptedText = this.state.promptedWords.join(" ");
    post("/report_progress", {
      id: this.state.id,
      typed: this.state.typedWords.join(" "),
      prompt: promptedText,
    });
  };

  requestProgress = async () => {
    const progress = await post("/request_progress", {
      targets: this.state.playerList,
    });
    this.setState({
      progress,
    });
    if (progress.every(([x]) => x === 1.0)) {
      clearInterval(this.multiplayerTimer);
      this.fastestWords();
    }
  };

  fastestWords = async () => {
    const fastestWords = await post("/fastest_words", {
      targets: this.state.playerList,
      prompt: this.state.promptedWords.join(" "),
    });
    this.setState({ fastestWords });
  };

  popPrevWord = () => {
    if (this.state.typedWords.length !== 0) {
      const out = this.state.typedWords[this.state.typedWords.length - 1];
      this.setState((state) => ({
        typedWords: state.typedWords.slice(0, state.typedWords.length - 1),
      }));
      return out;
    } else {
      return "";
    }
  };

  handleWordTyped = (word) => {
    if (!word) {
      return true;
    }

    const wordIndex = this.state.typedWords.length;

    const afterWordTyped = () => {
      this.updateReadouts();
      if (this.state.mode === Mode.MULTI) {
        this.reportProgress();
      }
    };

    this.setState((state) => {
      if (state.autoCorrect && word !== state.promptedWords[wordIndex]) {
        post("/autocorrect", { word }).then((data) => {
          // eslint-disable-next-line no-shadow
          this.setState((state) => {
            if (state.typedWords[wordIndex] !== word) {
              return {};
            }
            const { typedWords } = state;
            typedWords[wordIndex] = data;
            return { typedWords };
          });
        });
      }
      return {
        typedWords: state.typedWords.concat([word]),
        currWord: "",
      };
    }, afterWordTyped);

    return true;
  };

  handleChange = async (currWord) => {
    this.setState({ currWord });
    if (
      this.state.typedWords.length + 1 === this.state.promptedWords.length &&
      this.state.promptedWords[this.state.promptedWords.length - 1] ===
        currWord &&
      (this.state.mode === Mode.SINGLE ||
        this.state.typedWords.concat([currWord]).join(" ") ===
          this.state.promptedWords.join(" "))
    ) {
      clearInterval(this.timer);
      this.setState({ inputActive: false });
      this.handleWordTyped(currWord);
      const token = Cookies.get("token") || null;
      const { eligible, needVerify } = await post(
        "/check_leaderboard_eligibility",
        {
          user: Cookies.get("user"),
          wpm: this.state.wpm,
          token,
        }
      );
      const { wpm } = await this.updateReadouts();
      this.setState({ wpm }, () => {
        if (eligible && this.state.accuracy === 100) {
          this.setState({ showUsernameEntry: true, needVerify });
        }
      });
    } else if (!this.timer) {
      this.restart();
    }
  };

  handlePigLatinToggle = () => {
    this.initialize();
    this.setState((state) => ({
      autoCorrect: false,
      pigLatin: !state.pigLatin,
    }));
  };

  handleAutoCorrectToggle = () => {
    this.initialize();
    this.setState((state) => ({
      autoCorrect: !state.autoCorrect,
      pigLatin: false,
    }));
  };

  setMode = (mode) => {
    this.setState({ mode });
    if (mode === Mode.WAITING) {
      this.multiplayerTimer = setInterval(this.requestMatch, 1000);
    }
  };

  requestMatch = async () => {
    const data = await post("/request_match", { id: this.state.id });
    if (data.start) {
      this.setState({
        mode: Mode.MULTI,
        playerList: data.players,
        numPlayers: data.players.length,
        promptedWords: data.text.split(" "),
        progress: new Array(data.players.length).fill([0, 0]),
        pigLatin: false,
        autoCorrect: false,
      });
      clearInterval(this.multiplayerTimer);
      this.multiplayerTimer = setInterval(this.requestProgress, 500);
    } else {
      this.setState({
        numPlayers: data.numWaiting,
      });
    }
  };

  toggleLeaderBoard = () => {
    this.setState(({ showLeaderboard }) => ({
      showLeaderboard: !showLeaderboard,
    }));
  };

  handleSetTopics = (topics) => {
    this.setState({ topics }, this.initialize);
  };

  handleUsernameSubmission = async (name) => {
    await post("/record_wpm", {
      name,
      user: Cookies.get("user"),
      wpm: this.state.wpm,
      token: Cookies.get("token") || null,
    });
    this.hideUsernameEntry();
  };

  hideUsernameEntry = () => {
    this.setState({ showUsernameEntry: false });
  };

  render() {
    const {
      wpm,
      accuracy,
      numPlayers,
      startTime,
      currTime,
      playerList,
      id,
      fastestWords,
    } = this.state;
    const remainingTime = (currTime - startTime).toFixed(1);
    const playerIndex = playerList.indexOf(id);

    return (
      <>
        <div className="App container" id="app-root">
          <div className="row">
            <div className="col">
              <br />
              <div className="LeaderboardButton">
                <Button
                  onClick={() => this.toggleLeaderBoard(false)}
                  variant="outline-dark"
                >
                  Leaderboard
                </Button>
              </div>
              <h1 className="display-4 mainTitle">
                {/* eslint-disable-next-line react/jsx-one-expression-per-line */}
                <b>C</b>S61A <b>A</b>utocorrected <b>T</b>yping <b>S</b>oftware
              </h1>
              <br />
              <Indicators
                wpm={wpm}
                accuracy={accuracy}
                remainingTime={remainingTime}
              />
              {this.state.mode === Mode.MULTI && (
                <ProgressBars
                  numPlayers={numPlayers}
                  progress={this.state.progress}
                  playerIndex={playerIndex}
                />
              )}
              <br />
              <Prompt
                promptedWords={this.state.promptedWords}
                typedWords={this.state.typedWords}
                currWord={this.state.currWord}
              />
              <br />
              <Input
                key={this.state.promptedWords[0]}
                correctWords={this.state.promptedWords}
                words={this.state.typedWords}
                onWordTyped={this.handleWordTyped}
                onChange={this.handleChange}
                popPrevWord={this.popPrevWord}
                active={this.state.inputActive}
              />
              <br />
              {this.state.mode !== Mode.MULTI && (
                <>
                  <Options
                    pigLatin={this.state.pigLatin}
                    onPigLatinToggle={this.handlePigLatinToggle}
                    autoCorrect={this.state.autoCorrect}
                    onAutoCorrectToggle={this.handleAutoCorrectToggle}
                    onRestart={this.initialize}
                  />
                  <br />
                  <TopicPicker onClick={this.handleSetTopics} />
                </>
              )}
              {this.state.mode === Mode.MULTI && (
                <FastestWordsDisplay
                  playerIndex={playerIndex}
                  fastestWords={fastestWords}
                />
              )}
            </div>
          </div>
        </div>
        <OpeningDialog
          show={this.state.mode === Mode.WELCOME}
          setMode={this.setMode}
          toggleFindingOpponents={this.toggleFindingOpponents}
        />
        <LoadingDialog
          show={this.state.mode === Mode.WAITING}
          numPlayers={this.state.numPlayers}
        />
        <Leaderboard
          show={this.state.showLeaderboard}
          onHide={this.toggleLeaderBoard}
        />
        <HighScorePrompt
          key={this.state.showUsernameEntry}
          wpm={this.state.wpm}
          show={this.state.showUsernameEntry}
          needVerify={this.state.needVerify}
          onHide={this.hideUsernameEntry}
          onSubmit={this.handleUsernameSubmission}
        />
      </>
    );
  }
}

export default App;
