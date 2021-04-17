import { RUN_LARK_CODE } from "../constants/communicationEnums";
import LarkClient from "./larkClient";

export default function receive(arg) {
  if (arg.type === RUN_LARK_CODE) {
    new LarkClient(arg.key).start(arg.code);
  }
}
