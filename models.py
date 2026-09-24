from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Union


class StepRole(str, Enum):
    WARMUP = "warmup"
    INTERVAL = "interval"
    RECOVERY = "recovery"
    COOLDOWN = "cooldown"
    OTHER = "other"


class EndType(str, Enum):
    DISTANCE = "distance"
    TIME = "time"
    LAP_BUTTON = "lap_button"


class DistanceUnit(str, Enum):
    METER = "m"
    KILOMETER = "km"


class TargetKind(str, Enum):
    NONE = "none"
    HEART_RATE_RANGE = "heart_rate_range"
    HEART_RATE_ZONE = "heart_rate_zone"
    PACE_RANGE = "pace_range"


@dataclass(frozen=True)
class Target:
    kind: TargetKind
    min_bpm: Optional[int] = None
    max_bpm: Optional[int] = None
    zone_number: Optional[int] = None
    pace_fast_seconds_per_km: Optional[float] = None
    pace_slow_seconds_per_km: Optional[float] = None

    def __post_init__(self):
        if self.kind == TargetKind.NONE:
            if (
                self.min_bpm is not None
                or self.max_bpm is not None
                or self.zone_number is not None
                or self.pace_fast_seconds_per_km is not None
                or self.pace_slow_seconds_per_km is not None
            ):
                raise ValueError(
                    "A target NONE cannot contain heart-rate values."
                )

        elif self.kind == TargetKind.HEART_RATE_RANGE:
            if self.min_bpm is None or self.max_bpm is None:
                raise ValueError(
                    "Heart-rate target requires min_bpm and max_bpm."
                )

            if self.zone_number is not None:
                raise ValueError(
                    "Heart-rate range cannot contain zone_number."
                )

            if (
                self.pace_fast_seconds_per_km is not None
                or self.pace_slow_seconds_per_km is not None
            ):
                raise ValueError(
                    "Heart-rate range cannot contain pace values."
                )

            if self.min_bpm <= 0 or self.max_bpm <= 0:
                raise ValueError(
                    "Heart-rate values must be greater than zero."
                )

            if self.min_bpm >= self.max_bpm:
                raise ValueError(
                    "min_bpm must be lower than max_bpm."
                )

        elif self.kind == TargetKind.HEART_RATE_ZONE:
            if self.zone_number not in {1, 2, 3, 4, 5}:
                raise ValueError(
                    "Heart-rate zone must be between 1 and 5."
                )

            if self.min_bpm is not None or self.max_bpm is not None:
                raise ValueError(
                    "Heart-rate zone cannot contain min/max bpm."
                )

            if (
                self.pace_fast_seconds_per_km is not None
                or self.pace_slow_seconds_per_km is not None
            ):
                raise ValueError(
                    "Heart-rate zone cannot contain pace values."
                )

        elif self.kind == TargetKind.PACE_RANGE:
            if (
                self.pace_fast_seconds_per_km is None
                or self.pace_slow_seconds_per_km is None
            ):
                raise ValueError(
                    "Pace target requires fast and slow pace limits."
                )

            if (
                self.min_bpm is not None
                or self.max_bpm is not None
                or self.zone_number is not None
            ):
                raise ValueError(
                    "Pace target cannot contain heart-rate values."
                )

            if (
                self.pace_fast_seconds_per_km <= 0
                or self.pace_slow_seconds_per_km <= 0
            ):
                raise ValueError(
                    "Pace values must be greater than zero."
                )

            if (
                self.pace_fast_seconds_per_km
                >= self.pace_slow_seconds_per_km
            ):
                raise ValueError(
                    "Fast pace must be faster than slow pace."
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

    @classmethod
    def heart_rate_zone(cls, zone_number: int):
        return cls(
            kind=TargetKind.HEART_RATE_ZONE,
            zone_number=zone_number,
        )

    @classmethod
    def pace_range(
        cls,
        fast_seconds_per_km: float,
        slow_seconds_per_km: float,
    ):
        return cls(
            kind=TargetKind.PACE_RANGE,
            pace_fast_seconds_per_km=fast_seconds_per_km,
            pace_slow_seconds_per_km=slow_seconds_per_km,
        )


@dataclass
class Step:
    role: StepRole
    end_type: EndType
    value: Optional[float] = None
    target: Target = field(default_factory=Target.none)
    preferred_unit: Optional[DistanceUnit] = None

    def __post_init__(self):
        if self.end_type in {EndType.DISTANCE, EndType.TIME}:
            if self.value is None or self.value <= 0:
                raise ValueError(
                    "Distance/time step value must be greater than zero."
                )

        if self.end_type == EndType.DISTANCE:
            if self.preferred_unit is None:
                self.preferred_unit = DistanceUnit.METER

        elif self.end_type == EndType.TIME:
            if self.preferred_unit is not None:
                raise ValueError(
                    "Time-based steps cannot have a distance preferred unit."
                )

        elif self.end_type == EndType.LAP_BUTTON:
            if self.value is not None:
                raise ValueError(
                    "Lap-button steps do not accept a user-entered value."
                )

            if self.preferred_unit is not None:
                raise ValueError(
                    "Lap-button steps cannot have a distance preferred unit."
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
