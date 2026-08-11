"""Pole Descent Cognitive Test. The only paradigm this app ships."""

from __future__ import annotations

from acquisition.trial_state_machine import KeypressStopCondition, TrialStopCondition
from paradigms.paradigm import Paradigm, ReasonCode


class PDCTParadigm(Paradigm):
    def __init__(self, keymap: dict[str, str], reason_code_labels: dict[str, str]) -> None:
        """``keymap`` and ``reason_code_labels`` come from config.toml
        `[keymap]` / `[reason_code_labels]` -- never hardcoded here.
        """
        self._reason_codes = tuple(
            ReasonCode(key=key, code=code, label=reason_code_labels[code])
            for key, code in keymap.items()
        )

    @property
    def name(self) -> str:
        return "pdct"

    @property
    def reason_codes(self) -> tuple[ReasonCode, ...]:
        return self._reason_codes

    def default_stop_condition(self) -> TrialStopCondition:
        return KeypressStopCondition()
