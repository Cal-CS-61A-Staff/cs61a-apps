function ChatBox({ currentUser, id, mode, messages }) {
  const [typed, setTyped] = React.useState("");

  const historyRef = React.useRef();

  const handleChange = (e) => {
    setTyped(e.target.value);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      postMessage();
    }
  };

  const postMessage = () => {
    if (!typed.trim()) {
      return;
    }
    app.makeRequest("send_chat_message", {
      content: typed,
      mode,
      id,
    });
    setTyped("");
  };

  const scrollDown = () => {
    $('[data-toggle="tooltip"]').tooltip();
    historyRef.current.scrollTop = historyRef.current.scrollHeight;
  };

  React.useEffect(scrollDown, [messages]);

  function formatTooltip(message, omitUsername = false) {
    if (!message.created) return message.user.name;
    let time = moment.utc(message.created).local().format("ddd hh:mmA");
    if (omitUsername) return time;
    return `${message.user.name} | ${time}`;
  }

  const body = messages.map((message, i) => {
    const { user, body } = message;
    if (user.id === currentUser.id) {
      return (
        <div className="my-chat-bubble">
          <div
            className="chat-text"
            data-toggle="tooltip"
            data-placement="right"
            title={formatTooltip(message, true)}
          >
            {body}
          </div>
        </div>
      );
    } else if (messages[i + 1] && user.id === messages[i + 1].user.id) {
      return (
        <div className="chat-bubble">
          <div className="chat-icon none">{user.shortName[0]}</div>
          <div
            className="chat-text"
            data-toggle="tooltip"
            data-placement="right"
            title={formatTooltip(message)}
          >
            {body}
          </div>
        </div>
      );
    } else {
      return (
        <div className="chat-bubble">
          <div className="chat-icon">{user.shortName[0]}</div>
          <div
            className="chat-text"
            data-toggle="tooltip"
            data-placement="right"
            title={formatTooltip(message)}
          >
            {body}
          </div>
        </div>
      );
    }
  });

  return (
    <div className="panel panel-default">
      <div className="panel-heading">Chat️</div>
      <div className="panel-body">
        <div className="chat-history" ref={historyRef}>
          {body}
        </div>
        <div className="input-group chat-input">
          <input
            type="text"
            className="form-control"
            placeholder="Type a message..."
            onChange={handleChange}
            onKeyPress={handleKeyPress}
            value={typed}
          />
          <div className="input-group-btn">
            <button
              className="btn btn-default"
              type="button"
              onClick={postMessage}
            >
              <span className="glyphicon glyphicon-play" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
