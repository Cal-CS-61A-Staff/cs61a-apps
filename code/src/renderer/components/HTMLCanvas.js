/* eslint-disable react/no-array-index-key */
import React, { useRef, useEffect } from "react";

export default function HTMLCanvas({ layers, draw }) {
  const rendererCanvasesRef = useRef(Array(layers));
  const baseCanvasesRef = useRef(null);

  const deltaX = useRef(-1500);
  const deltaY = useRef(-1000);

  if (baseCanvasesRef.current === null) {
    baseCanvasesRef.current = Array(layers)
      .fill()
      .map(() => document.createElement("canvas"));
    for (const canvas of baseCanvasesRef.current) {
      canvas.width = 3000;
      canvas.height = 2000;
    }
  }

  function updateRenderCanvases() {
    const baseCanvases = baseCanvasesRef.current;
    const renderCanvases = rendererCanvasesRef.current;
    for (let i = 0; i !== layers; ++i) {
      const baseCanvas = baseCanvases[i];
      const renderCanvas = renderCanvases[i];
      const ctx = renderCanvas.getContext("2d");

      ctx.clearRect(0, 0, renderCanvas.width, renderCanvas.height);
      ctx.drawImage(baseCanvas, deltaX.current, deltaY.current);
    }
  }

  useEffect(() => {
    deltaX.current = Math.round(
      rendererCanvasesRef.current[0].parentNode.offsetWidth / 2 - 1500
    );
    deltaY.current = Math.round(
      rendererCanvasesRef.current[0].parentNode.offsetHeight / 2 - 1000
    );
  }, [rendererCanvasesRef.current]);

  useEffect(() => {
    draw(baseCanvasesRef.current);
    updateRenderCanvases();
  });

  useEffect(() => {
    const topRenderCanvas = rendererCanvasesRef.current[layers - 1];

    let prevCursorOffsetX;
    let prevCursorOffsetY;
    let isDragging = false;

    function mouseDownHandler(e) {
      prevCursorOffsetX = e.clientX;
      prevCursorOffsetY = e.clientY;
      isDragging = true;
    }

    function mouseMoveHandler(e) {
      if (isDragging) {
        deltaX.current += e.clientX - prevCursorOffsetX;
        deltaY.current += e.clientY - prevCursorOffsetY;
        prevCursorOffsetX = e.clientX;
        prevCursorOffsetY = e.clientY;

        updateRenderCanvases();
      }
    }
    function mouseUpHandler() {
      isDragging = false;
    }

    topRenderCanvas.addEventListener("mousedown", mouseDownHandler);
    topRenderCanvas.addEventListener("mousemove", mouseMoveHandler);
    topRenderCanvas.addEventListener("mouseup", mouseUpHandler);

    return () => {
      topRenderCanvas.removeEventListener("mousedown", mouseDownHandler);
      topRenderCanvas.removeEventListener("mousemove", mouseMoveHandler);
      topRenderCanvas.removeEventListener("mouseup", mouseUpHandler);
    };
  }, [rendererCanvasesRef.current]);

  const canvasLayers = Array(layers)
    .fill()
    .map((_, i) => (
      <canvas
        className="canvasLayer"
        width={3000}
        height={2000}
        key={i}
        ref={(elem) => {
          rendererCanvasesRef.current[i] = elem;
        }}
      >
        {i}
      </canvas>
    ));

  return <div className="canvas">{canvasLayers}</div>;
}
