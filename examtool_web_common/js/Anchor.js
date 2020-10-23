import React from "react";

export default function Anchor({ name }) {
  const style = {
    display: "block",
    position: "relative",
    top: -70,
    visibility: "hidden",
  };
  // eslint-disable-next-line jsx-a11y/anchor-is-valid,jsx-a11y/anchor-has-content
  return <a style={style} name={name} />;
}
