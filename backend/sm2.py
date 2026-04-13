from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

RATING_AGAIN = "again"
RATING_HARD = "hard"
RATING_GOOD = "good"
RATING_EASY = "easy"

RATING_TO_QUALITY = {
    RATING_AGAIN: 0,
    RATING_HARD: 2,
    RATING_GOOD: 4,
    RATING_EASY: 5,
}

MIN_EASE_FACTOR = 1.3
LEITNER_BOX_THRESHOLDS = [0, 3, 7, 14, 30]


@dataclass
class SM2State:
    interval: int
    repetitions: int
    ease_factor: float
    next_review: datetime
    leitner_box: int
    is_mastered: bool


def compute_next_state(
    interval: int,
    repetitions: int,
    ease_factor: float,
    rating: str,
) -> SM2State:
    quality = RATING_TO_QUALITY[rating]
    now = datetime.now(timezone.utc)

    if quality < 3:
        new_repetitions = 0
        new_interval = 1
        new_ease_factor = ease_factor
    else:
        new_repetitions = repetitions + 1
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(interval * ease_factor)

        ease_delta = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        new_ease_factor = max(MIN_EASE_FACTOR, ease_factor + ease_delta)

        if rating == RATING_EASY:
            new_interval = round(new_interval * 1.3)

    new_next_review = now + timedelta(days=new_interval)
    new_leitner_box = interval_to_leitner_box(new_interval)
    new_is_mastered = new_leitner_box == 5

    return SM2State(
        interval=new_interval,
        repetitions=new_repetitions,
        ease_factor=round(new_ease_factor, 4),
        next_review=new_next_review,
        leitner_box=new_leitner_box,
        is_mastered=new_is_mastered,
    )


def interval_to_leitner_box(interval: int) -> int:
    for box, threshold in enumerate(LEITNER_BOX_THRESHOLDS, start=1):
        if interval <= threshold:
            return box
    return 5


def is_due(next_review: datetime) -> bool:
    return datetime.now(timezone.utc) >= next_review.replace(tzinfo=timezone.utc)
