// @flow strict

import * as React from "react";

import Badge from "react-bootstrap/Badge";

type Props = {
  tags: Array<string>,
};

export default function Tags({ tags }: Props) {
  return (
    <>
      {tags.map((tag) => (
        <Badge className="float-right" pill variant="primary" key={tag}>
          {tag}
        </Badge>
      ))}
    </>
  );
}
