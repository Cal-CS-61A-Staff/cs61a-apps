/* eslint-disable react/no-array-index-key */
// @flow strict

import "bootstrap/dist/css/bootstrap.css";
import moment from "moment";
import { useContext, useEffect, useState } from "react";
import * as React from "react";
import Col from "react-bootstrap/Col";
import Table from "react-bootstrap/Table";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import { Link, Redirect } from "react-router-dom";
import AttendanceRow from "./AttendanceRow";
import type { ID, PersonDetails } from "./models";
import { sectionTitle } from "./models";
import StateContext from "./StateContext";
import useAPI from "./useAPI";

type Props = {
  userID?: ID,
};

export default function HistoryPage({ userID }: Props): React.Node {
  const { currentUser } = useContext(StateContext);
  const [loadedUser, setLoadedUser] = useState<?PersonDetails>(null);

  const fetchUser = useAPI("fetch_user", setLoadedUser);

  useEffect(() => {
    if (userID != null) {
      fetchUser({ user_id: userID });
    }
  }, [userID, fetchUser]);

  if (
    (userID == null) === (currentUser?.isStaff === true) ||
    currentUser == null
  ) {
    return <Redirect to="/" />;
  }

  const user = userID == null ? currentUser : loadedUser;

  if (user == null) {
    return null;
  }

  return (
    <Container>
      <br />
      <Row>
        <Col>
          <h2>{user.name}</h2>
          <p className="lead">
            {" "}
            <a href={`mailto:${user.email}`}>{user.email}</a>
          </p>
          <Table hover>
            <thead>
              <tr className="text-center">
                <th>Date</th>
                <th>Section</th>
                <th>Attendance</th>
              </tr>
            </thead>
            <tbody>
              {user.attendanceHistory.map(({ section, session, status }, i) => (
                <tr key={i} className="text-center">
                  <td className="align-middle">
                    <b>{moment.unix(session.startTime).format("MMMM D")}</b>
                  </td>
                  <td className="align-middle">
                    {section != null && currentUser.isStaff ? (
                      <Link to={`/section/${section.id}`}>
                        {sectionTitle(section)}
                      </Link>
                    ) : (
                      sectionTitle(section)
                    )}
                  </td>
                  <td>
                    <AttendanceRow editable={false} status={status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Col>
      </Row>
    </Container>
  );
}
