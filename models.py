from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Union


class StepRole(str, Enum):
    WARMUP = "warmup"
    INTERVAL = "interval"
    RECOVERY = "recovery"
    COOLDOWN = "cooldown"


class EndType(str, Enum):
    DISTANCE = "distance"
    TIME = "time"


class DistanceUnit(str, Enum):
    METER = "m"
    KILOMETER = "km"


class TargetKind(str, Enum):
    NONE = "none"
    HEART_RATE_RANGE = "heart_rate_range"


@dataclass(frozen=True)
class Target:
    kind: TargetKind
    min_bpm: Optional[int] = None
    max_bpm: Optional[int] = None

    def __post_init__(self):
        if self.kind == TargetKind.NONE:
            if self.min_bpm is not None or self.max_bpm is not None:
                raise ValueError(
                    "A target NONE cannot contain heart-rate values."
                )

        elif self.kind == TargetKind.HEART_RATE_RANGE:
            if self.min_bpm is None or self.max_bpm is None:
                raise ValueError(
                    "Heart-rate target requires min_bpm and max_bpm."
                )

            if self.min_bpm <= 0 or self.max_bpm <= 0:
                raise ValueError(
                    "Heart-rate values must be greater than zero."
                )

            if self.min_bpm >= self.max_bpm:
                raise ValueError(
                    "min_bpm must be lower than max_bpm."
                )

    @classmethod
    def none(cls):
        return cls(kind=TargetKind.NONE)

    @classmethod
    def heart_rate(cls, min_bpm: int, max_bpm: int):
        return cls(
            kind=TargetKind.HEART_RATE_RANGE,
            min_bpm=min_bpm,
            max_bpm=max_bpm,
        )


@dataclass
class Step:
    role: StepRole
    end_type: EndType
    value: float
    target: Target = field(default_factory=Target.none)
    preferred_unit: Optional[DistanceUnit] = None

    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("Step value must be greater than zero.")

        if self.end_type == EndType.DISTANCE:
            if self.preferred_unit is None:
                self.preferred_unit = DistanceUnit.METER

        elif self.end_type == EndType.TIME:
            if self.preferred_unit is not None:
                raise ValueError(
                    "Time-based steps cannot have a distance preferred unit."
                )


@dataclass
class RepeatBlock:
    repetitions: int
    steps: List[Step]

    def __post_init__(self):
        if self.repetitions <= 0:
            raise ValueError(
                "Repeat count must be greater than zero."
            )

        if not self.steps:
            raise ValueError(
                "RepeatBlock must contain at least one step."
            )


WorkoutItem = Union[Step, RepeatBlock]


@dataclass
class Workout:
    name: str
    steps: List[WorkoutItem]

    def __post_init__(self):
        self.name = self.name.strip()

        if not self.name:
            raise ValueError("Workout name cannot be empty.")

        if not self.steps:
            raise ValueError(
                "Workout must contain at least one step."
            )
