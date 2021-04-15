import $ from "jquery";

import GoldenLayout from "imports-loader?$=jquery!golden-layout";
import "golden-layout/src/css/goldenlayout-base.css";
import "golden-layout/src/css/goldenlayout-dark-theme.css";

let layout;
const containers = {
  output: [],
  editor: [],
  debugger: [],
  terminal: [],
  okResults: [],
  graphics: [],
};

let numContainersOpen = 0;

let onAllClosed;

export function checkAllClosed() {
  if (numContainersOpen === 0) {
    onAllClosed();
  }
}

let initContainer;

export function initGoldenLayout(callback) {
  onAllClosed = callback;

  layout = new GoldenLayout(
    {
      settings: {
        showPopoutIcon: false,
        showMaximiseIcon: false,
        showCloseIcon: false,
      },
      dimensions: {
        borderWidth: 5,
        minItemHeight: 10,
        minItemWidth: 10,
        headerHeight: 30,
        dragProxyWidth: 300,
        dragProxyHeight: 200,
      },
      content: [
        {
          type: "column",
          content: [
            {
              type: "component",
              componentName: "dummy",
              componentState: {
                callback: (container) => {
                  initContainer = container;
                },
              },
            },
          ],
        },
      ],
    },
    $("#tabRoot")
  );

  $(window).resize(() => {
    layout.updateSize($(window).width(), $(window).height() - 30);
  });

  layout.registerComponent("dummy", dummyComponent);
  layout.init();
  console.log(initContainer);
}

export function requestContainer(position, targetDim, type, friends) {
  if (initContainer) {
    initializeContainer(initContainer, type);
    const ret = initContainer;
    initContainer = null;
    return ret;
  }

  let orientation;
  let tryFirst;

  if (position === "left" || position === "right") {
    orientation = "row";
    tryFirst = position === "left";
  } else {
    orientation = "column";
    tryFirst = position === "top";
  }

  let outputContainer;

  const config = {
    type: "component",
    componentName: "dummy",
    componentState: {
      callback: (container) => {
        outputContainer = container;
      },
    },
    height: 40,
    width: 20,
  };

  const stackedConfig = {
    type: "stack",
    height: 40,
    width: 20,
    content: [config],
  };

  let ok;

  for (const friend of friends) {
    if (containers[friend].length === 0) {
      continue;
    }
    const lastElem = Array.from(containers[friend]).pop();
    lastElem.parent.parent.addChild(config);
    ok = true;
    break;
  }

  if (!ok) {
    if (layout.root.contentItems[0].config.type !== orientation) {
      const oldRoot = layout.root.contentItems[0];
      const newRoot = layout.createContentItem({
        type: orientation,
        content: [],
      });
      layout.root.replaceChild(oldRoot, newRoot);
      newRoot.addChild(oldRoot);
      if (tryFirst) {
        newRoot.addChild(stackedConfig, 0);
      } else {
        newRoot.addChild(stackedConfig);
      }
    } else if (tryFirst) {
      layout.root.contentItems[0].addChild(stackedConfig, 0);
    } else {
      layout.root.contentItems[0].addChild(stackedConfig);
    }
  }

  if (orientation === "row") {
    stackedConfig.width = targetDim;
  } else {
    stackedConfig.height = targetDim;
  }
  layout.updateSize();

  // noinspection JSUnusedAssignment
  initializeContainer(outputContainer, type);

  // noinspection JSUnusedAssignment
  return outputContainer;
}

function initializeContainer(container, type) {
  containers[type].push(container);
  ++numContainersOpen;
  container.on("destroy", () => {
    containers[type] = containers[type].filter((obj) => obj !== container);
    --numContainersOpen;
  });
}

function dummyComponent(container, state) {
  state.callback(container);
}
