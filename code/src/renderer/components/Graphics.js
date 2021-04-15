import React, { useRef } from "react";

import glWrap from "../utils/glWrap.js";
import HTMLCanvas from "./HTMLCanvas.js";

function makeColorString([r, g, b]) {
  return `rgb(${r}, ${g}, ${b})`;
}

function x(val) {
  return val + 1500;
}

function y(val) {
  return -val + 1000;
}

function draw(bgCanvas, mainCanvas, turtleCanvas, data, currIndex) {
  const bgCtx = bgCanvas.getContext("2d");
  const ctx = mainCanvas.getContext("2d");
  const turtleCtx = turtleCanvas.getContext("2d");

  // eslint-disable-next-line no-param-reassign
  for (; currIndex.current !== data.length; ++currIndex.current) {
    const [command, ...params] = data[currIndex.current];
    if (command === "draw_rectangular_line") {
      const [[startX, startY, endX, endY], color, width] = params;
      ctx.beginPath();
      ctx.lineWidth = width;
      ctx.strokeStyle = makeColorString(color);
      ctx.moveTo(x(startX), y(startY));
      ctx.lineTo(x(endX), y(endY));
      ctx.stroke();
    } else if (command === "draw_circle") {
      const [
        [centerX, centerY, radius],
        color,
        width,
        isFilled,
        startAngle,
        endAngle,
      ] = params;
      ctx.beginPath();
      ctx.lineWidth = width;
      ctx.strokeStyle = makeColorString(color);
      ctx.fillStyle = makeColorString(color);
      ctx.arc(x(centerX), y(centerY), radius, -endAngle, -startAngle);
      ctx.stroke();
      if (isFilled) {
        ctx.fill();
      }
    } else if (command === "fill_path") {
      const [path, color] = params;
      ctx.beginPath();
      ctx.fillStyle = makeColorString(color);
      for (const [movement, ...dest] of path) {
        switch (movement) {
          case "line": {
            const [[pointX, pointY]] = dest;
            ctx.lineTo(x(pointX), y(pointY));
            break;
          }
          case "arc": {
            const [[centerX, centerY], radius, startAngle, endAngle] = dest;
            ctx.arc(
              x(centerX),
              y(centerY),
              radius,
              -startAngle,
              -endAngle,
              endAngle > startAngle
            );
            break;
          }
          default:
            console.error("Unknown movement:", movement);
        }
      }
      ctx.fill();
    } else if (command === "axis_aligned_rectangle") {
      const [[cornerX, cornerY], width, height, color] = params;
      ctx.beginPath();
      ctx.fillStyle = makeColorString(color);
      ctx.rect(x(cornerX), y(cornerY), width, -height);
      ctx.fill();
    } else if (command === "set_bgcolor") {
      const [color] = params;
      bgCtx.fillStyle = makeColorString(color);
      bgCtx.fillRect(0, 0, mainCanvas.width, mainCanvas.height);
    } else if (command === "clear") {
      bgCtx.clearRect(0, 0, bgCanvas.width, bgCanvas.height);
      ctx.clearRect(0, 0, mainCanvas.width, mainCanvas.height);
      turtleCtx.clearRect(0, 0, turtleCanvas.width, turtleCanvas.height);
    } else if (command === "refreshed_turtle") {
      turtleCtx.clearRect(0, 0, turtleCanvas.width, turtleCanvas.height);
      const [turtleData] = params;
      if (turtleData === null) {
        continue;
      }
      const [[turtleX, turtleY], angle, scaleX, scaleY] = turtleData;
      turtleCtx.save();
      turtleCtx.translate(x(turtleX), y(turtleY));
      turtleCtx.rotate(-angle);
      turtleCtx.beginPath();
      turtleCtx.fillStyle = makeColorString([0, 0, 0]);
      turtleCtx.moveTo(-5 * scaleX, 5 * scaleY);
      turtleCtx.lineTo(-5 * scaleX, -5 * scaleY);
      turtleCtx.lineTo(0, 0);
      turtleCtx.fill();
      turtleCtx.restore();
    } else {
      console.error(`Ignoring unknown graphics command ${command}`);
    }
  }
}

function Graphics({ data }) {
  const currIndex = useRef(0);
  return (
    <HTMLCanvas
      layers={3}
      draw={([bgCanvas, mainCanvas, turtleCanvas]) =>
        draw(bgCanvas, mainCanvas, turtleCanvas, data, currIndex)
      }
    />
  );
}

export default glWrap(Graphics, "right", 50, "graphics", []);
