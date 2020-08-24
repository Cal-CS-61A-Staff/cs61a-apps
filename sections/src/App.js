/* eslint-disable react/no-array-index-key */
// @flow strict

import { useEffect, useState } from "react";
import * as React from "react";
import Container from "react-bootstrap/Container";

import Nav from "react-bootstrap/Nav";
import Navbar from "react-bootstrap/Navbar";
import NavDropdown from "react-bootstrap/NavDropdown";
import { BrowserRouter as Router, Link, Route, Switch } from "react-router-dom";
import MainPage from "./MainPage";

import "bootstrap/dist/css/bootstrap.css";
import type { ID, State } from "./models";
import SectionPage from "./SectionPage";
import StateContext from "./StateContext";
import useAPI from "./useAPI";

export default function App(): React.Node {
  const [state, setState] = useState<?State>(null);

  const updateState = (newState: State) => {
    // preserve ordering of sections, if possible
    if (state == null || newState.sections.length !== state?.sections.length) {
      setState(newState);
      return;
    }
    const sections = Array(newState.sections.length);
    const lookup = new Map<ID, number>();
    state.sections.forEach((section, i) => lookup.set(section.id, i));
    let ok = true;
    newState.sections.forEach((section) => {
      const i = lookup.get(section.id);
      if (i == null) {
        ok = false;
        return;
      }
      sections[i] = section;
    });
    if (ok) {
      // eslint-disable-next-line no-param-reassign
      newState.sections = sections;
    }
    setState(newState);
  };

  const refreshState = useAPI("refresh_state", updateState);

  useEffect(() => {
    if (state == null) {
      refreshState();
    }
  }, [state, refreshState]);

  if (state == null) {
    return null;
  }

  return (
    <Router>
      <Navbar bg="info" variant="dark" expand="md">
        <Link to="/">
          <Navbar.Brand>CS 61A Tutorials</Navbar.Brand>
        </Link>
        <Navbar.Toggle aria-controls="navbar" />
        <Navbar.Collapse id="navbar">
          <Nav className="mr-auto">
            <Link to="/" className="nav-link active">
              Home
            </Link>
            <Link to="/history" className="nav-link active">
              History
            </Link>
            <Nav.Link
              href="https://cs61a.org/tutors.html"
              target="_blank"
              active
            >
              Staff
            </Nav.Link>
            <Nav.Link
              href="https://oh.cs61a.org/appointments"
              target="_blank"
              active
            >
              Appointments
            </Nav.Link>
            {state.currentUser?.isStaff && (
              <Nav.Link href="/admin" active>
                Admin
              </Nav.Link>
            )}
          </Nav>
          <Nav className="mr-sm-2">
            {state.currentUser != null ? (
              <NavDropdown title={state.currentUser.name} active>
                <NavDropdown.Item href="/oauth/logout">
                  Log out
                </NavDropdown.Item>
              </NavDropdown>
            ) : null}
          </Nav>
        </Navbar.Collapse>
      </Navbar>
      <StateContext.Provider value={{ ...state, updateState }}>
        <Switch>
          <Route exact path="/">
            <MainPage />
          </Route>
          <Route path="/history">TODO: History</Route>
          <Route path="/admin">TODO: Admin</Route>
          <Route path="/section/:id">
            {({ match }) => <SectionPage id={match.params.id} />}
          </Route>
          <Route path="*">
            <Container>Error: Page not found</Container>
          </Route>
        </Switch>
      </StateContext.Provider>
    </Router>
  );
}
