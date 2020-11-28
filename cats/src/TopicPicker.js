import React, { useState } from "react";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";

import "./TopicPicker.css";

export default function TopicPicker({ onClick }) {
  const [topics, setTopics] = useState("");

  const handleChange = (e) => {
    setTopics(e.target.value);
  };

  const handleClick = () => {
    onClick(
      topics
        .split(/\s|,/)
        .map((x) => x.trim().toLowerCase())
        .filter((x) => x.length)
    );
  };

  return (
    <div className="TopicPicker">
      <Form
        onSubmit={(e) => {
          e.preventDefault();
          handleClick();
        }}
      >
        <Form.Label>Specify topics of interest</Form.Label>
        <Form.Row>
          <Col>
            <Form.Control
              placeholder="Cat, Cats, Kittens, ..."
              value={topics}
              onChange={handleChange}
            />
          </Col>
          <Button variant="primary" onClick={handleClick}>
            Submit
          </Button>
        </Form.Row>
        <Form.Text className="text-muted">
          List topics separated by commas.
        </Form.Text>
      </Form>
    </div>
  );
}
