"""MAN OF THE YEAR -- deterministic reference state transition model.

Runnable Python specification of selected narrative invariants, not Android/Unreal implementation.
No third-party libraries. Does not contain copyrighted/locked lines of dialogue.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Literal
import json

Outcome = Literal['APPROACH', 'PASS']

class TransitionError(ValueError):
    pass

@dataclass
class NarrativeState:
    save_schema_version: int = 1
    completed_chapters: list[int] = field(default_factory=list)
    decisions: dict[str, str] = field(default_factory=dict)
    approached_at: str | None = None
    first_meeting_wiola_present: bool = False
    missed_opportunities: int = 0
    january_closed: bool = False
    paulina_quests_unlocked: bool = False
    paulina_at_icecream_shop: bool = False
    ch59_canonical_event_played: bool = False
    campaign_completion_count: int = 0
    completed_run_ids: list[str] = field(default_factory=list)
    unlocks: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if self.save_schema_version != 1:
            raise TransitionError('unsupported save version')
        if self.missed_opportunities not in range(5):
            raise TransitionError('invalid missed opportunities')
        if self.approached_at is not None and self.approached_at not in {f'PAU-OP{i}' for i in range(1,5)}:
            raise TransitionError('unknown meeting id')
        if self.first_meeting_wiola_present and self.approached_at != 'PAU-OP1':
            raise TransitionError('Wiola is present only at the first encounter scene')
        if self.paulina_quests_unlocked != (self.approached_at is not None):
            raise TransitionError('quest unlock mismatch')
        if self.ch59_canonical_event_played and not self.paulina_at_icecream_shop:
            raise TransitionError('CH59 required Paulina present')
        if len(set(self.completed_run_ids)) != len(self.completed_run_ids):
            raise TransitionError('duplicate completion IDs')
        if self.campaign_completion_count != len(self.completed_run_ids):
            raise TransitionError('completion count inconsistent')
        if sorted(set(self.completed_chapters)) != self.completed_chapters:
            raise TransitionError('chapter progression inconsistent')
        if any(not (1 <= n <= 70) for n in self.completed_chapters):
            raise TransitionError('invalid chapter index')

    def record_paulina_opportunity(self, opportunity_number: int, choice: Outcome) -> None:
        if opportunity_number not in range(1, 5):
            raise TransitionError('invalid opportunity number')
        if choice not in ('APPROACH', 'PASS'):
            raise TransitionError('invalid choice')
        event_id = f'PAU-OP{opportunity_number}'
        if event_id in self.decisions:
            if self.decisions[event_id] != choice:
                raise TransitionError('contradictory decision cannot overwrite checkpoint')
            return
        expected = 1 + sum(k.startswith('PAU-OP') for k in self.decisions)
        if opportunity_number != expected:
            raise TransitionError('encounters must be visited chronologically')
        if self.january_closed:
            raise TransitionError('January already closed')
        self.decisions[event_id] = choice
        if choice == 'APPROACH' and self.approached_at is None:
            self.approached_at = event_id
            self.first_meeting_wiola_present = opportunity_number == 1
            self.paulina_quests_unlocked = True
        elif choice == 'PASS' and self.approached_at is None:
            self.missed_opportunities += 1
        if opportunity_number == 4:
            self.january_closed = True
        self.validate()

    def enter_chapter59(self) -> str:
        if not self.january_closed:
            raise TransitionError('January scenes must be resolved before CH59')
        self.paulina_at_icecream_shop = True
        self.ch59_canonical_event_played = True
        self.validate()
        return 'KNOWN_CUSTOMER' if self.approached_at is not None else 'FIRST_MEETING_CUSTOMER'

    def complete_main_campaign(self, run_id: str) -> bool:
        if not run_id or not run_id.strip() or len(run_id) > 128:
            raise TransitionError('invalid run ID')
        if run_id in self.completed_run_ids:
            return False
        if self.completed_chapters != list(range(1, 71)):
            raise TransitionError('not all canonical chapters completed')
        if not self.ch59_canonical_event_played:
            raise TransitionError('required CH59 event missing')
        self.completed_run_ids.append(run_id)
        self.campaign_completion_count = len(self.completed_run_ids)
        idx = self.campaign_completion_count
        if idx <= 3:
            self.unlocks.append(f'DLC-{idx:02}')
        self.validate()
        return True

    def encode(self) -> str:
        self.validate()
        return json.dumps(asdict(self), sort_keys=True, ensure_ascii=False)

    @classmethod
    def decode(cls, raw: str) -> 'NarrativeState':
        try:
            obj = json.loads(raw)
            if not isinstance(obj, dict):
                raise TransitionError('save must be a JSON object')
            allowed = set(cls.__dataclass_fields__)
            if set(obj) != allowed:
                raise TransitionError('save fields are not schema-compatible')
            state = cls(**obj)
            state.validate()
            return state
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            if isinstance(exc, TransitionError):
                raise
            raise TransitionError('invalid save data') from exc
