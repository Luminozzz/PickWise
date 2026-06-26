from algorithm import config
from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable

class Hand_Size(Enum):
    LARGE = 'large'
    MEDIUM = 'medium'
    SMALL = 'small'

class Game_Type(Enum):
    MMORPG = 'mmorpg'
    FPS = 'fps'
    RTS = 'rts'
    MOBA = 'moba'
    NOT_MENTIONED = 'none_of_the_above'

class Preferability(Enum):
    YES = "yes"
    PREFERABLY = "preferably"
    NO ="no"

class RuleType(Enum):
    HARD = "hard"
    SOFT = "soft"

class Usage(Enum):
    MOST_OF_THE_TIME = "most_of_the_time"
    OFTEN = "often"
    OCCASIONALLY = "occasionally"
    RARELY = "rarely"
    NEVER = "never"

class User_Type(Enum):
    GAMER = "gamer"
    OFFICE_WORKER = "office_worker"
    STUDENT = "student"

@dataclass
class UserPreferences:
    hand_size: Hand_Size | None
    wireless: Preferability | None
    budget: tuple[int, int] | None
    left_hand: bool | None
    user_type: User_Type | None

@dataclass
class Student(UserPreferences):
    travel_portability: Usage | None
    extra_buttons: Preferability | None

@dataclass
class Office_Worker(UserPreferences):
    hours_worked: Usage | None
    extra_buttons: Preferability | None

@dataclass
class Gamer(UserPreferences):
    type_of_game: Game_Type | None
    light_weight: bool | None
    rgb: bool | None

@dataclass
class Bundle:
    candidates: list
    passed_hard_rules: list
    failed_hard_rules: list
    score: float = 0.0

    @property
    def priority(self) -> tuple:
        return (len(self.passed_hard_rules), self.score)


@dataclass
class Rule:
    id: str
    rule_type: Callable[[dict], RuleType] | RuleType
    description: str
    applicable_to_users: bool | Callable[[dict], bool] # Is it relevant to the user?
    mouse_compatibility: bool | Callable[[dict, Any], bool] # Does the mouse have this feature that the rules need?
    weight: float | Callable[[dict, Any], float] = 0.0 # Weight can either be fixed or calculated
    explanation: str | Callable[[dict, Any], str] = "" # Static message or dynamic per-mouse reason

    def points(self, facts: dict, candidate: Any) -> float:
        if callable(self.weight):
            return float(self.weight(facts, candidate))
        return float(self.weight)

    def explain(self, facts: dict, candidate: Any) -> str:
        if callable(self.explanation):
            return self.explanation(facts, candidate)
        return self.explanation
    




