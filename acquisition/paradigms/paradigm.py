"""Paradigm ABC: what varies between PDCT and any future task.

A paradigm supplies its reason-code keymap (already loaded from config by the
caller) and the default trial stop condition. It does not own trial timing
guards (that's TrialStateMachine, paradigm-agnostic) or GUI layout.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from acquisition.trial_state_machine import TrialStopCondition


@dataclass(frozen=True)
class ReasonCode:
    """One hotkey-triggerable annotation: key, machine code, human label."""

    key: str
    code: str
    label: str


class Paradigm(ABC):
    """Defines a task's identity and annotation vocabulary.

    New paradigms (e.g. the maze task) implement this and supply their own
    ``config.toml`` `[keymap]` / `[reason_code_labels]` tables -- no source
    changes elsewhere (acquisition/CLAUDE.md "Trial annotation").
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def reason_codes(self) -> tuple[ReasonCode, ...]: ...

    @abstractmethod
    def default_stop_condition(self) -> TrialStopCondition:
        """The stop condition new trials start with. PDCT: keypress-driven.
        A future pose-driven paradigm returns a different implementation here
        without the GUI or TrialStateMachine changing (invariant 8).
        """
        ...
