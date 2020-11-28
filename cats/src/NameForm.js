import React, { useRef } from "react";

export default function NameForm({ onSubmit }) {
  const inputRef = useRef(null);

  return (
    <>
      Congratulations! Your WPM is fast enough to place on our leaderboard!
      Enter a name here to associate it with your score:
      <br />
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit(inputRef.current.value);
        }}
      >
        <div className="form-group">
          <input
            type="text"
            ref={inputRef}
            className="form-control"
            id="exampleInputEmail1"
            aria-describedby="emailHelp"
            placeholder="Enter username"
          />
          <small id="emailHelp" className="form-text text-muted">
            Please don't name yourself anything inappropriate!
          </small>
        </div>
        <div className="form-group">
          <button type="submit" className="btn btn-primary">
            Submit
          </button>
        </div>
      </form>
    </>
  );
}
