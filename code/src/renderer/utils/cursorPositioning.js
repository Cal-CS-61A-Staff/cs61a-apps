/* eslint-disable no-param-reassign */
function createRange(node, chars, range) {
  if (!range) {
    range = document.createRange();
    range.selectNode(node);
    range.setStart(node, 0);
  }

  if (chars.count === 0) {
    range.setEnd(node, chars.count);
  } else if (node && chars.count > 0) {
    if (node.nodeType === Node.TEXT_NODE) {
      if (node.textContent.length < chars.count) {
        chars.count -= node.textContent.length;
      } else {
        range.setEnd(node, chars.count);
        chars.count = 0;
      }
    } else {
      for (let lp = 0; lp < node.childNodes.length; lp++) {
        range = createRange(node.childNodes[lp], chars, range);

        if (chars.count === 0) {
          break;
        }
      }
    }
  }

  return range;
}

export function setCurrentCursorPosition(node, chars) {
  if (chars >= 0) {
    const selection = window.getSelection();

    const range = createRange(node, { count: chars });

    if (range) {
      range.collapse(false);
      selection.removeAllRanges();
      selection.addRange(range);
    }
  }
}
function isChildOf(node, parent) {
  while (node !== null) {
    if (node === parent) {
      return true;
    }
    node = node.parentNode;
  }

  return false;
}

export function getCurrentCursorPosition(parent) {
  const selection = window.getSelection();
  let charCount = -1;
  let node;

  if (selection.focusNode) {
    if (isChildOf(selection.focusNode, parent)) {
      node = selection.focusNode;
      charCount = selection.focusOffset;

      while (node) {
        if (node === parent) {
          break;
        }

        if (node.previousSibling) {
          node = node.previousSibling;
          charCount += node.textContent.length;
        } else {
          node = node.parentNode;
          if (node === null) {
            break;
          }
        }
      }
    }
  }

  return charCount;
}
