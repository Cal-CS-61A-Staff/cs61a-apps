/* eslint-disable react/no-array-index-key */
import React from "react";
import CardListElement from "./CardListElement.js";

export default function CardList({ header, items, onClick, selectedIndex }) {
  const cards = items.map((name, index) => (
    <CardListElement
      key={index}
      name={name}
      onClick={() => onClick(index)}
      selected={index === selectedIndex}
    />
  ));

  return (
    <div className="modalCol browserFileSelector">
      {header}
      {cards}
    </div>
  );
}
