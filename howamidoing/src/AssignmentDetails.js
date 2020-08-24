import React, { useState, useEffect, useMemo } from "react";
import $ from "jquery";
import _ from "lodash";

import { Row, Col } from "react-bootstrap";
import { Slider } from "@material-ui/core";
import Dropdown from "./Dropdown";
import ScoreHistogram from "./ScoreHistogram";

import StudentTable from "./StudentTable.js";

import { getAssignmentLookup, getAssignments } from "./loadAssignments.js";
import { extend } from "./StudentView";
import computeTotals from "./computeTotals.js";

const showScore = (score, rangeMin, rangeMax, TAToShow, TA) =>
  (TAToShow === "All" || TAToShow === TA) &&
  score <= rangeMax &&
  score >= rangeMin;

const extractAssignmentData = (arr, index, TA, TAs, rangeMin, rangeMax) =>
  arr
    .map((scores) => scores[index])
    .filter((score, i) => showScore(score, rangeMin, rangeMax, TA, TAs[i]));

// note: mutates data
const addAssignmentTotals = (data, assignments, topics) => {
  for (let student = 0; student < data.length; ++student) {
    let scores = {};
    const header = data[student];
    for (const title of Object.keys(header)) {
      if (assignments[title]) {
        scores[title] = header[title];
      }
    }
    scores = extend(scores, assignments);
    const totals = computeTotals(topics, scores, false);
    for (const assignment of Object.keys(totals)) {
      header[assignment] = totals[assignment];
    }
  }
  return data;
};

const updateBins = (value, setRangeMin, setRangeMax) => {
  setRangeMin(value[0]);
  setRangeMax(value[1]);
};

const round = (x) => Math.round((x + Number.EPSILON) * 100) / 100;

export default function AssignmentDetails({ onLogin }) {
  const [data, setData] = useState([]);
  const [assignmentIndex, setAssignmentIndex] = useState(0);

  window.setSchema([], []);

  const assignments = useMemo(getAssignmentLookup, [data]);

  useEffect(() => {
    $.post("/allScores").done(({ header: newHeader, scores }) => {
      window.setSchema(newHeader, []);
      const assignmentData = scores.map((x) =>
        Object.fromEntries(x.map((v, i) => [newHeader[i], v]))
      );
      const newData = addAssignmentTotals(
        assignmentData,
        getAssignmentLookup(),
        getAssignments()
      );
      setData(newData);
    });
  }, []);

  const assignmentNames = Object.keys(assignments);

  const currentAssignmentName = assignmentNames[assignmentIndex];
  const assignment = assignments[currentAssignmentName];
  console.log("Assignment is ", assignment);
  const assignmentScores = useMemo(
    () =>
      data.map((student) =>
        assignmentNames
          .map((assignmentName) => student[assignmentName] || 0)
          .map((x) => Number.parseFloat(x))
      ),
    [data, assignmentNames]
  );

  const maxScore = assignment.futureMaxScore || 0;

  const [rangeMin, setRangeMin] = useState(0);
  const [rangeMax, setRangeMax] = useState(maxScore);

  const binSize = (rangeMax - rangeMin) / 20;
  const defaultBins = [0, 1, 2, 3, 4, 5];
  const bins =
    assignment.futureMaxScore && assignment.futureMaxScore !== Infinity
      ? _.range(rangeMin, rangeMax + 0.01, binSize).map(round)
      : defaultBins;
  console.log("BINS ARE ", bins);
  useEffect(() => {
    setRangeMax(Math.min(rangeMax, bins[bins.length - 1]));
  }, [assignmentIndex]);

  const TAs = data.map((x) => x.TA).concat(["All"]);
  const TANames = Array.from(new Set(TAs));
  const [TA, setTA] = useState("All");
  const students = data
    .map((x, student) => ({
      ...x,
      Score: assignmentScores[student][assignmentIndex],
    }))
    .filter((student) =>
      showScore(student.Score, rangeMin, rangeMax, TA, student.TA)
    );

  const contents = (
    <>
      <ScoreHistogram
        students={students}
        bins={bins}
        extractedData={extractAssignmentData(
          assignmentScores,
          assignmentIndex,
          TA,
          TAs,
          rangeMin,
          rangeMax
        )}
      />
      <Row>
        <Dropdown value={currentAssignmentName} onChange={setAssignmentIndex}>
          {assignmentNames}
        </Dropdown>
        <Dropdown value={TA} onChange={(i) => setTA(TANames[i])}>
          {TANames}
        </Dropdown>
      </Row>
      <Row>
        <Col md={3}>
          <Slider
            min={0}
            max={
              assignment.futureMaxScore &&
              assignment.futureMaxScore !== Infinity
                ? assignment.futureMaxScore
                : 0
            }
            value={[rangeMin, rangeMax]}
            valueLabelDisplay="auto"
            onChange={(__, values) =>
              updateBins(values, setRangeMin, setRangeMax)
            }
          />
        </Col>
      </Row>
      <StudentTable students={students} onLogin={onLogin} />
    </>
  );

  return data.length ? contents : <div>Loading...</div>;
}
