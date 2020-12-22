import $ from "jquery";
import _ from "lodash";

import { getAssignmentLookup, getAssignments } from "./loadAssignments.js";
import { extend } from "./StudentView";
import computeTotals from "./computeTotals.js";

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

export default function buildExportURI() {
  var assignments, data;

  $.ajax("/allScores", { async: false, method: "POST" }).done(
    ({ header, scores }) => {
      window.setSchema(header, []);
      const assignmentData = scores.map((x) =>
        Object.fromEntries(x.map((v, i) => [header[i], v]))
      );
      const newData = addAssignmentTotals(
        assignmentData,
        getAssignmentLookup(),
        getAssignments()
      );
      assignments = getAssignmentLookup();
      data = newData;
    }
  );

  const assignmentNames = Object.keys(assignments);
  const studentData = ["Name", "Email", "SID"];

  const assignment = assignments["Raw Score"];
  console.log("Assignment is ", assignment);
  const assignmentScores = data.map((student) => [
    ...studentData.map((metadata) => student[metadata] || 0),
    ...assignmentNames
      .map((assignmentName) => student[assignmentName] || 0)
      .map((x) => Number.parseFloat(x)),
  ]);

  const combinedData = [
    [...studentData, ...assignmentNames],
    ...assignmentScores,
  ];

  const csvContent =
    "data:text/csv;charset=utf-8," +
    combinedData.map((e) => e.join(",")).join("\n");

  return encodeURI(csvContent);
}
