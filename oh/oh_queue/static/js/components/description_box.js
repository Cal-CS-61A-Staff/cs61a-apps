function DescriptionBox({
  editable,
  locked,
  state,
  ticket,
  prompt,
  placeholder,
  description,
  onChange,
  onSubmit,
}) {
  let staff = isStaff(state);

  if ((!editable && staff) || locked) {
    return (
      <p className="ticket-view-desc">
        {ticket.description ? ticket.description : <i>No description</i>}
      </p>
    );
  } else {
    return (
      <div>
        <h4>{prompt}</h4>
        <textarea
          className="description-box"
          value={description}
          onChange={(e) => onChange(e.target.value)}
          rows="5"
          placeholder={placeholder}
        />
        {description !== ticket.description ? (
          <button
            onClick={onSubmit}
            className="description-button btn btn-default btn-lg btn-block"
          >
            {" "}
            Save Description{" "}
          </button>
        ) : null}
      </div>
    );
  }
}
