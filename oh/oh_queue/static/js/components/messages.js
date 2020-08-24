let Messages = ({messages}) =>
  <div className="row messages">
    {messages.map((message) => <Message key={message.id} message={message}/>)}
  </div>;

let Message = ({message}) => {
  let {id, text, category, visible} = message;
  if (!visible) {
    return null;
  }
  return (
    <div className="col-xs-12">
      <div className={`alert alert-${category} alert-dismissible`} role="alert">
        <button type="button" className="close" aria-label="Close"
          onClick={() => app.clearMessage(id)}>
          <span aria-hidden="true">&times;</span>
        </button>
        { text }
      </div>
    </div>
  );
};
