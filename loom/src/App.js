import React, { useState } from "react";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import "./App.css";
import FormControl from "react-bootstrap/FormControl";
import InputGroup from "react-bootstrap/InputGroup";
import Row from "react-bootstrap/Row";

import "bootstrap/dist/css/bootstrap.min.css";

function App() {
  const [urls, setUrls] = useState([]);

  const [enteredURL, setEnteredURL] = useState("");

  const handleClick = () => {
    const id = enteredURL.match(/share\/([a-z0-9]+)/)[1];
    const processedURL = `https://www.loom.com/embed/${id}`;
    setUrls(urls.concat([processedURL]));
    setEnteredURL("");
  };

  return (
    <Container fluid>
      <Row>
        <Col>
          <h1>Loom Viewer</h1>
        </Col>
      </Row>
      <Row>
        <Col>
          <InputGroup className="mb-3">
            <FormControl
              placeholder="https://www.loom.com/share/abcdefg"
              aria-label="Loom URL"
              aria-describedby="basic-addon2"
              value={enteredURL}
              onChange={(e) => setEnteredURL(e.target.value)}
            />
            <InputGroup.Append>
              <Button onClick={handleClick} variant="outline-secondary">
                Add
              </Button>
            </InputGroup.Append>
          </InputGroup>
        </Col>
      </Row>
      <div style={{ width: "100%", display: "flex", flexWrap: "wrap" }}>
        {urls.map((url) => (
          <LoomView key={url} url={url} />
        ))}
      </div>
    </Container>
  );
}

function LoomView({ url }) {
  const [hidden, setHidden] = useState(false);

  if (hidden) {
    return null;
  }

  return (
    <div style={{ position: "relative" }}>
      <button
        style={{ position: "absolute", top: 0, right: 0 }}
        className="btn btn-danger"
        onClick={() => setHidden(true)}
      >
        &times;
      </button>
      <iframe
        style={{ width: 550, height: 300 }}
        src={url}
        frameBorder="0"
        allowFullScreen
      />
    </div>
  );
}

export default App;
