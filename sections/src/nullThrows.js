// @flow strict

export default function nullThrows<T>(t: ?T): T {
  if (t == null) {
    throw Error("Expected input to be nonnull");
  }
  return t;
}
