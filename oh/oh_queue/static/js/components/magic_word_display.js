class MagicWordDisplay extends React.Component {
  constructor(...args) {
    super(...args);

    this.state = {
      loaded: false,
      oldMagicWord: undefined,
      magicWord: undefined,
      refreshInterval: null
    };

    this.loadState = this.loadState.bind(this);

    this.loadState();
  }

  loadState() {
    if (this.state.loaded) return;
    var config = this.props.state.config;
    if (!this.props.state.loaded || !config) {
      setTimeout(this.loadState, 100);
      return;
    }
    if (isStaff(this.props.state) && config.queue_magic_word_mode !== 'none') {
      if (this.state.refreshInterval) {
        clearInterval(this.state.refreshInterval);
        this.state.refreshInterval = null;
      }
      this.setState({
        refreshInterval: setInterval(() => {
          let mode = this.props.state.config.queue_magic_word_mode;
          if (mode !== 'timed_numeric'
            && (mode !== 'none' || this.state.magicWord !== undefined)) return
          app.makeRequest('refresh_magic_word', (res) => {
            let magicWord = res.magic_word || null;
            this.setState({
              oldMagicWord: this.state.magicWord,
              magicWord: magicWord
            });
          });
        }, 10000)
      });
    }
    this.setState({
      loaded: true
    });
  }

  componentWillUnmount() {
    if (this.state.refreshInterval) {
      clearInterval(this.state.refreshInterval);
      this.state.refreshInterval = null;
    }
  }

  render() {
    if (!this.state.loaded) {
      this.loadState();
      return false;
    }
    if (this.props.state.config.queue_magic_word_mode === 'none'
      || this.state.magicWord === undefined) {
      return false;
    }

    let magicWordElem = (<i>Loading...</i>);
    if (this.state.magicWord) {
      let magicWord = this.state.magicWord;
      magicWordElem = (<code>{ magicWord }</code>);
    }

    return (
      <div>
        <h4>Magic word: { magicWordElem }</h4>
      </div>
    );
  }
}
