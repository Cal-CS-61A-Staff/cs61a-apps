import LarkClient from "../web/larkClient";

export default function test(code, onSuccess, onError) {
  const client = new LarkClient();
  client
    .test(code)
    .then(onSuccess)
    .catch((e) => onError(e.toString()));
  return client.stop;
}
