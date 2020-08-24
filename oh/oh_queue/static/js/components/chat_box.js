function ChatBox({ currentUser, socket, id, mode }) {
    const [messages, setMessages] = React.useState([[{
        shortName: "?", name: "OH Queue Bot"
    },
        "This chat is unreliable and only for if you can't connect to Zoom." +
        " Otherwise, use the Zoom chat!"]]);

    const [typed, setTyped] = React.useState("");

    const historyRef = React.useRef();

    const handleChange = (e) => {
        setTyped(e.target.value);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            postMessage()
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
        $('[data-toggle="tooltip"]').tooltip()
        historyRef.current.scrollTop = historyRef.current.scrollHeight;
    };

    React.useEffect(scrollDown, [messages]);

    React.useEffect(() => {
        socket.on("chat_message", (message) => {
            if (message.mode !== mode || message.id !== id) {
                return;
            }
            setMessages(messages.concat([[message.sender, message.content]]));
        });
        return () => socket.removeAllListeners("chat_message");
    }, [messages]);

    const body = messages.map(([sender, message], i) => {
        if (sender.id === currentUser.id) {
            return (
                <div className="my-chat-bubble">
                    <div className="chat-text">{message}</div>
                </div>
            )
        } else if (messages[i + 1] && sender.id === messages[i + 1][0].id) {
            return (
                <div className="chat-bubble">
                    <div className="chat-icon none">{sender.shortName[0]}</div>
                    <div className="chat-text" data-toggle="tooltip" data-placement="right" title={sender.name}>{message}</div>
                </div>
            )
        } else {
            return (
                <div className="chat-bubble">
                    <div className="chat-icon">{sender.shortName[0]}</div>
                    <div className="chat-text" data-toggle="tooltip" data-placement="right" title={sender.name}>{message}</div>
                </div>
            )
        }
    });

    return (
        <div className="panel panel-default">
            <div className="panel-heading">⚠️ Emergency Backup Chat ⚠️</div>
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
                        <button className="btn btn-default" type="button" onClick={postMessage}>
                            <span className="glyphicon glyphicon-play" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
