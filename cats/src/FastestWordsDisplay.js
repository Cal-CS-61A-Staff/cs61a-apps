import React from "react";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import Table from "react-bootstrap/Table";

export default function FastestWordsDisplay({ fastestWords, playerIndex }) {
  return (
    fastestWords.length > 0 && (
      <>
        <h4>Fastest words typed by each player</h4>
        <Row>
          {fastestWords.map((words, i) => (
            <Col>
              <Table striped bordered hover>
                <thead>
                  <tr>
                    <th>
                      Player {i + 1}
                      {playerIndex === i && " (you)"}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {words.map((word) => (
                    <tr>
                      <td>{word}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Col>
          ))}
        </Row>
      </>
    )
  );
}
