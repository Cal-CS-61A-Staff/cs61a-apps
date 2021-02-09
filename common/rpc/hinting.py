from __future__ import annotations
from typing import Dict, List, Optional, TypedDict

from common.rpc.utils import create_service

service = create_service(__name__, "deploy.hosted")


class Messages(TypedDict):
    file_contents: Dict[str, str]
    grading: Dict[str, GradingInfo]
    hinting: HintingInfo
    ...


class RequiredGradingInfo(TypedDict):
    passed: int
    failed: int
    locked: int


class GradingInfo(RequiredGradingInfo, total=False):
    failed_outputs: List[str]


class HintingInfo(TypedDict):
    flagged: bool
    question: HintQuestionInfo
    ...


class HintQuestionInfo(TypedDict):
    pre_prompt: str
    name: str
    ...


class WWPDHintOutput(TypedDict):
    hints: List[str]


class HintOutput(TypedDict):
    message: str
    post_prompt: Optional[str]


@service.route("/api/wwpd_hints")
def get_wwpd_hints(*, unlock_id: str, selected_options: List[str]) -> WWPDHintOutput:
    ...


@service.route("/api/hints")
def get_hints(
    *, assignment: str, test: str, messages: Messages, user: str
) -> HintOutput:
    ...
