from models import (
    DistanceUnit,
    EndType,
    RepeatBlock,
    Step,
    StepRole,
    TargetKind,
    Workout,
)


STEP_TYPES = {
    StepRole.WARMUP: {
        "stepTypeId": 1,
        "stepTypeKey": "warmup",
        "displayOrder": 1,
    },
    StepRole.COOLDOWN: {
        "stepTypeId": 2,
        "stepTypeKey": "cooldown",
        "displayOrder": 2,
    },
    StepRole.INTERVAL: {
        "stepTypeId": 3,
        "stepTypeKey": "interval",
        "displayOrder": 3,
    },
    StepRole.RECOVERY: {
        "stepTypeId": 4,
        "stepTypeKey": "recovery",
        "displayOrder": 4,
    },
    StepRole.OTHER: {
        "stepTypeId": 7,
        "stepTypeKey": "other",
        "displayOrder": 7,
    },
}


REPEAT_STEP_TYPE = {
    "stepTypeId": 6,
    "stepTypeKey": "repeat",
    "displayOrder": 6,
}


DISTANCE_END_CONDITION = {
    "conditionTypeId": 3,
    "conditionTypeKey": "distance",
    "displayOrder": 3,
    "displayable": True,
}


TIME_END_CONDITION = {
    "conditionTypeId": 2,
    "conditionTypeKey": "time",
    "displayOrder": 2,
    "displayable": True,
}


LAP_BUTTON_END_CONDITION = {
    "conditionTypeId": 1,
    "conditionTypeKey": "lap.button",
    "displayOrder": 1,
    "displayable": True,
}


# VALIDATED_REFERENCE: exact value observed in the Garmin reference JSON.
# Keep this literal until our generated LAP variant is imported successfully.
LAP_BUTTON_REFERENCE_VALUE = 1000.0


ITERATIONS_END_CONDITION = {
    "conditionTypeId": 7,
    "conditionTypeKey": "iterations",
    "displayOrder": 7,
    "displayable": False,
}


DISTANCE_UNITS = {
    DistanceUnit.METER: {
        "unitId": 1,
        "unitKey": "meter",
        "factor": 100.0,
    },
    DistanceUnit.KILOMETER: {
        "unitId": 2,
        "unitKey": "kilometer",
        "factor": 100000.0,
    },
}


NO_TARGET = {
    "workoutTargetTypeId": 1,
    "workoutTargetTypeKey": "no.target",
    "displayOrder": 1,
}


HEART_RATE_TARGET = {
    "workoutTargetTypeId": 4,
    "workoutTargetTypeKey": "heart.rate.zone",
    "displayOrder": 4,
}


EMPTY_STROKE_TYPE = {
    "strokeTypeId": 0,
    "strokeTypeKey": None,
    "displayOrder": 0,
}


EMPTY_EQUIPMENT_TYPE = {
    "equipmentTypeId": 0,
    "equipmentTypeKey": None,
    "displayOrder": 0,
}


RUNNING_SPORT_TYPE = {
    "sportTypeId": 1,
    "sportTypeKey": "running",
    "displayOrder": 1,
}


EMPTY_AUTHOR = {
    "userProfilePk": None,
    "displayName": None,
    "fullName": None,
    "profileImgNameLarge": None,
    "profileImgNameMedium": None,
    "profileImgNameSmall": None,
    "userPro": False,
    "vivokidUser": False,
}


def build_end_condition(step: Step):
    if step.end_type == EndType.DISTANCE:
        return (
            DISTANCE_END_CONDITION.copy(),
            float(step.value),
            DISTANCE_UNITS[step.preferred_unit].copy(),
        )

    if step.end_type == EndType.TIME:
        return TIME_END_CONDITION.copy(), float(step.value), None

    if step.end_type == EndType.LAP_BUTTON:
        return (
            LAP_BUTTON_END_CONDITION.copy(),
            LAP_BUTTON_REFERENCE_VALUE,
            None,
        )

    raise ValueError(f"Unsupported end type: {step.end_type}")


def build_target(step: Step):
    if step.target.kind == TargetKind.NONE:
        return {
            "targetType": NO_TARGET.copy(),
            "targetValueOne": None,
            "targetValueTwo": None,
            "targetValueUnit": None,
            "zoneNumber": None,
        }

    if step.target.kind == TargetKind.HEART_RATE_RANGE:
        return {
            "targetType": HEART_RATE_TARGET.copy(),
            "targetValueOne": float(step.target.min_bpm),
            "targetValueTwo": float(step.target.max_bpm),
            "targetValueUnit": None,
            "zoneNumber": None,
        }

    if step.target.kind == TargetKind.HEART_RATE_ZONE:
        return {
            "targetType": HEART_RATE_TARGET.copy(),
            "targetValueOne": None,
            "targetValueTwo": None,
            "targetValueUnit": None,
            "zoneNumber": step.target.zone_number,
        }

    raise ValueError(f"Unsupported target kind: {step.target.kind}")


def build_executable_step(
    step: Step,
    step_id,
    step_order: int,
    child_step_id=None,
):
    end_condition, end_condition_value, preferred_unit = build_end_condition(step)
    target = build_target(step)

    return {
        "type": "ExecutableStepDTO",
        "stepId": step_id,
        "stepOrder": step_order,
        "stepType": STEP_TYPES[step.role].copy(),
        "childStepId": child_step_id,
        "description": None,
        "endCondition": end_condition,
        "endConditionValue": end_condition_value,
        "preferredEndConditionUnit": preferred_unit,
        "endConditionCompare": None,
        **target,
        "secondaryTargetType": None,
        "secondaryTargetValueOne": None,
        "secondaryTargetValueTwo": None,
        "secondaryTargetValueUnit": None,
        "secondaryZoneNumber": None,
        "endConditionZone": None,
        "strokeType": EMPTY_STROKE_TYPE.copy(),
        "equipmentType": EMPTY_EQUIPMENT_TYPE.copy(),
        "category": None,
        "exerciseName": None,
        "workoutProvider": None,
        "providerExerciseSourceId": None,
        "weightValue": None,
        "weightUnit": None,
    }


def build_repeat_group(
    repeat_block: RepeatBlock,
    step_id,
    step_order: int,
    child_step_id: int,
    child_step_ids,
    child_step_orders,
):
    if len(child_step_ids) != len(repeat_block.steps):
        raise ValueError(
            "child_step_ids length must match repeat block steps."
        )

    if len(child_step_orders) != len(repeat_block.steps):
        raise ValueError(
            "child_step_orders length must match repeat block steps."
        )

    workout_steps = []

    for step, child_id, child_order in zip(
        repeat_block.steps,
        child_step_ids,
        child_step_orders,
    ):
        workout_steps.append(
            build_executable_step(
                step=step,
                step_id=child_id,
                step_order=child_order,
                child_step_id=child_step_id,
            )
        )

    return {
        "type": "RepeatGroupDTO",
        "stepId": step_id,
        "stepOrder": step_order,
        "stepType": REPEAT_STEP_TYPE.copy(),
        "childStepId": child_step_id,
        "numberOfIterations": repeat_block.repetitions,
        "workoutSteps": workout_steps,
        "endConditionValue": float(repeat_block.repetitions),
        "preferredEndConditionUnit": None,
        "endConditionCompare": None,
        "endCondition": ITERATIONS_END_CONDITION.copy(),
        "skipLastRestStep": False,
        "smartRepeat": False,
    }


def count_required_step_ids(workout: Workout) -> int:
    total = 0

    for item in workout.steps:
        total += 1

        if isinstance(item, RepeatBlock):
            total += len(item.steps)

    return total


def build_workout_steps(workout: Workout, step_ids):
    expected = count_required_step_ids(workout)

    if len(step_ids) != expected:
        raise ValueError(
            f"Expected {expected} step IDs, received {len(step_ids)}."
        )

    ids = iter(step_ids)
    result = []
    step_order = 1
    repeat_group_number = 0

    for item in workout.steps:
        if isinstance(item, Step):
            result.append(
                build_executable_step(
                    step=item,
                    step_id=next(ids),
                    step_order=step_order,
                    child_step_id=None,
                )
            )
            step_order += 1
            continue

        if isinstance(item, RepeatBlock):
            repeat_group_number += 1

            group_step_id = next(ids)
            group_step_order = step_order
            step_order += 1

            child_step_ids = []
            child_step_orders = []

            for _ in item.steps:
                child_step_ids.append(next(ids))
                child_step_orders.append(step_order)
                step_order += 1

            result.append(
                build_repeat_group(
                    repeat_block=item,
                    step_id=group_step_id,
                    step_order=group_step_order,
                    child_step_id=repeat_group_number,
                    child_step_ids=child_step_ids,
                    child_step_orders=child_step_orders,
                )
            )
            continue

        raise TypeError(f"Unsupported workout item: {type(item)!r}")

    return result


def build_garmin_workout(
    workout: Workout,
    step_ids,
    description=None,
):
    workout_steps = build_workout_steps(workout, step_ids)

    return {
        "workoutId": None,
        "ownerId": None,
        "workoutName": workout.name,
        "description": description,
        "updatedDate": None,
        "createdDate": None,
        "sportType": RUNNING_SPORT_TYPE.copy(),
        "subSportType": None,
        "trainingPlanId": None,
        "author": EMPTY_AUTHOR.copy(),
        "sharedWithUsers": None,
        "estimatedDurationInSecs": None,
        "estimatedDistanceInMeters": None,
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": RUNNING_SPORT_TYPE.copy(),
                "poolLengthUnit": None,
                "poolLength": None,
                "avgTrainingSpeed": None,
                "estimatedDurationInSecs": None,
                "estimatedDistanceInMeters": None,
                "estimatedDistanceUnit": None,
                "estimateType": None,
                "description": None,
                "workoutSteps": workout_steps,
            }
        ],
        "poolLength": None,
        "poolLengthUnit": None,
        "locale": None,
        "workoutProvider": None,
        "workoutSourceId": None,
        "uploadTimestamp": None,
        "atpPlanId": None,
        "consumer": None,
        "consumerName": None,
        "consumerImageURL": None,
        "consumerWebsiteURL": None,
        "workoutNameI18nKey": None,
        "descriptionI18nKey": None,
        "avgTrainingSpeed": None,
        "estimateType": None,
        "estimatedDistanceUnit": None,
        "workoutThumbnailUrl": None,
        "isSessionTransitionEnabled": None,
        "shared": False,
    }
