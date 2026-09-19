from models import EndType, RepeatBlock, Step, StepRole, TargetKind


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


ITERATIONS_END_CONDITION = {
    "conditionTypeId": 7,
    "conditionTypeKey": "iterations",
    "displayOrder": 7,
    "displayable": False,
}


METER_UNIT = {
    "unitId": 1,
    "unitKey": "meter",
    "factor": 100.0,
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


def build_end_condition(step: Step):
    if step.end_type == EndType.DISTANCE:
        return DISTANCE_END_CONDITION.copy(), METER_UNIT.copy()

    if step.end_type == EndType.TIME:
        return TIME_END_CONDITION.copy(), None

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

    raise ValueError(f"Unsupported target kind: {step.target.kind}")


def build_executable_step(
    step: Step,
    step_id: int,
    step_order: int,
    child_step_id=None,
):
    end_condition, preferred_unit = build_end_condition(step)
    target = build_target(step)

    return {
        "type": "ExecutableStepDTO",
        "stepId": step_id,
        "stepOrder": step_order,
        "stepType": STEP_TYPES[step.role].copy(),
        "childStepId": child_step_id,
        "description": None,
        "endCondition": end_condition,
        "endConditionValue": float(step.value),
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
    step_id: int,
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
