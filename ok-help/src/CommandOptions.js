import React from "react";
import Category from "./Category.js";
import "./CommandOptions.css";

export default function CommandOptions(props) {
  const {
    activeIndex,
    setActiveIndex,
    selectedOptions,
    setSelectedOptions,
  } = props;

  const categories = props.options.map(
    // eslint-disable-next-line react/no-array-index-key
    (category, index) => (
      <Category
        category={category}
        key={index}
        active={index === activeIndex}
        onClick={() => setActiveIndex(index)}
        setOption={(option, val) => {
          selectedOptions[index][option] = val;
          setSelectedOptions({ ...selectedOptions });
        }}
      />
    )
  );
  return <div className="CommandOptions row">{categories}</div>;
}
