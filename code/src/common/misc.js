// eslint-disable-next-line import/prefer-default-export
export function randomString(length = 48) {
  return Array(length)
    .fill()
    .map(() =>
      String.fromCharCode(Math.floor(Math.random() * 26) + "a".charCodeAt(0))
    )
    .join("");
}
