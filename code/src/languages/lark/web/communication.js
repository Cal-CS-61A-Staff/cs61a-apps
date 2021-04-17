import { RUN_LARK_CODE } from "../constants/communicationEnums";
import LarkClient from "./larkClient";

export default async function receive(arg) {
  if (arg.type === RUN_LARK_CODE) {
    new LarkClient(arg.key, arg.code).start();
  }
}
