import React, { useState, useEffect } from "react";
import Cookies from "js-cookie";
import Modal from "react-bootstrap/Modal";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import post from "./post";

export default function EditName({ onNameChange }) {
  const [name, setName] = useState("");
  const [display, setDisplay] = useState(false);

  useEffect(() => {
    post("/check_on_leaderboard", { user: Cookies.get("user") }).then(
      setDisplay
    );
  }, [display]);

  const handleChange = (e) => {
    setName(e.target.value);
  };

  return (
    display && (
      <Modal.Footer>
        <Form
          onSubmit={(e) => {
            e.preventDefault();
            setName("");
            onNameChange(name);
          }}
          style={{ width: "100%" }}
        >
          <Form.Row>
            <Col>
              <Form.Control
                placeholder="Change leaderboard name"
                value={name}
                onChange={handleChange}
              />
            </Col>
            <Button variant="primary" type="submit">
              Submit
            </Button>
          </Form.Row>
        </Form>
      </Modal.Footer>
    )
  );
}
