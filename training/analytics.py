from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from django.conf import settings
from sklearn.linear_model import LinearRegression


PERIODS = {
    "day": ("День", "h"),
    "week": ("Тиждень", "D"),
    "month": ("Місяць", "D"),
    "year": ("Рік", "MS"),
}
ANSWER_FIELDS = ["correct_answers", "wrong_answers", "missed_signals"]


def period_bounds(period, now):
    zone = ZoneInfo(settings.TIME_ZONE)
    today = now.astimezone(zone).date()
    if period == "day":
        start = today
        previous_start = start - timedelta(days=1)
        end = start + timedelta(days=1)
    elif period == "week":
        start = today - timedelta(days=today.weekday())
        previous_start = start - timedelta(days=7)
        end = start + timedelta(days=7)
    elif period == "month":
        start = today.replace(day=1)
        previous_start = (start - timedelta(days=1)).replace(day=1)
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    else:
        start = today.replace(month=1, day=1)
        previous_start = start.replace(year=start.year - 1)
        end = start.replace(year=start.year + 1)
    return tuple(datetime.combine(date, time.min, tzinfo=zone) for date in (previous_start, start, end))


def prepare_results(documents):
    columns = ["mode", "created_at", "reaction_time_ms", *ANSWER_FIELDS]
    frame = pd.DataFrame(documents, columns=columns)
    # MongoDB зберігає BSON-дати в UTC, зокрема дати без tzinfo.
    frame["created_at"] = pd.to_datetime(
        frame["created_at"], utc=True, errors="coerce", format="mixed"
    )
    for field in ["reaction_time_ms", *ANSWER_FIELDS]:
        frame[field] = pd.to_numeric(frame[field], errors="coerce")
    return frame.dropna(subset=["created_at"]).sort_values("created_at", kind="stable")


def split_modes(frame):
    reaction = frame.loc[
        frame["mode"].eq("reaction")
        & frame["reaction_time_ms"].between(1, 60000)
        & frame["reaction_time_ms"].mod(1).eq(0)
    ].copy()
    answers = frame[ANSWER_FIELDS]
    valid_answers = (
        np.isfinite(answers).all(axis=1)
        & answers.ge(0).all(axis=1)
        & answers.mod(1).eq(0).all(axis=1)
    )
    concentration = frame.loc[
        frame["mode"].eq("concentration") & valid_answers
    ].copy()
    concentration["total_signals"] = concentration[ANSWER_FIELDS].sum(axis=1)
    concentration = concentration.loc[concentration["total_signals"] > 0]
    return reaction, concentration


def summarize(reaction, concentration):
    times = reaction["reaction_time_ms"].to_numpy(dtype=float)
    correct = float(np.sum(concentration["correct_answers"].to_numpy(dtype=float)))
    total = float(np.sum(concentration["total_signals"].to_numpy(dtype=float)))
    return {
        "reaction": {
            "count": int(times.size),
            "mean": float(np.mean(times)) if times.size else None,
            "best": float(np.min(times)) if times.size else None,
            "worst": float(np.max(times)) if times.size else None,
        },
        "concentration": {
            "count": len(concentration),
            "correct": int(correct),
            "total": int(total),
            "accuracy": 100 * correct / total if total else None,
        },
    }


def compare(current, previous, lower_is_better=False):
    result = {"current": current, "previous": previous, "difference": None}
    if current is None or previous is None:
        result["message"] = "Недостатньо даних для порівняння"
        return result
    difference = current - previous
    result["difference"] = difference
    if np.isclose(difference, 0, atol=1e-9):
        result["message"] = "Результат не змінився"
    elif (difference < 0) == lower_is_better:
        result["message"] = "Результат покращився"
    else:
        result["message"] = "Результат погіршився"
    return result


def reaction_trend(reaction):
    if len(reaction) < 5:
        return {"message": "Недостатньо даних для аналізу тенденції", "slope": None}
    numbers = np.arange(len(reaction)).reshape(-1, 1)
    model = LinearRegression().fit(numbers, reaction["reaction_time_ms"].to_numpy())
    slope = float(model.coef_[0])
    if abs(slope) < 1:
        message = "Час реакції майже не змінюється."
    elif slope < 0:
        message = "Час реакції має тенденцію до зменшення."
    else:
        message = "Час реакції має тенденцію до збільшення."
    return {"message": message, "slope": slope}


def chart_data(frame, frequency, mode):
    if frame.empty:
        return {"labels": [], "values": [], "rows": []}
    frame = frame.copy()
    frame["created_at"] = frame["created_at"].dt.tz_convert(settings.TIME_ZONE)
    groups = frame.groupby(pd.Grouper(key="created_at", freq=frequency))
    if mode == "reaction":
        values = groups["reaction_time_ms"].mean().dropna()
    else:
        counts = groups[["correct_answers", "total_signals"]].sum()
        counts = counts.loc[counts["total_signals"] > 0]
        values = 100 * counts["correct_answers"] / counts["total_signals"]
    date_format = "%d.%m.%Y %H:%M %z" if frequency == "h" else "%d.%m.%Y"
    if frequency == "MS":
        date_format = "%m.%Y"
    labels = values.index.strftime(date_format).tolist()
    numbers = [round(float(value), 2) for value in values]
    return {"labels": labels, "values": numbers, "rows": list(zip(labels, numbers))}


def analyze_results(documents, period, now):
    _, frequency = PERIODS[period]
    previous_start, start, end = period_bounds(period, now)
    frame = prepare_results(documents)
    dates = frame["created_at"]
    current_frame = frame.loc[(dates >= start) & (dates < end) & (dates <= now)]
    previous_frame = frame.loc[(dates >= previous_start) & (dates < start)]
    reaction, concentration = split_modes(current_frame)
    current = summarize(reaction, concentration)
    previous = summarize(*split_modes(previous_frame))
    return {
        "start": start,
        "end": end,
        "previous_start": previous_start,
        **current,
        "has_data": bool(len(reaction) or len(concentration)),
        "reaction_comparison": compare(
            current["reaction"]["mean"], previous["reaction"]["mean"], lower_is_better=True
        ),
        "concentration_comparison": compare(
            current["concentration"]["accuracy"], previous["concentration"]["accuracy"]
        ),
        "reaction_chart": chart_data(reaction, frequency, "reaction"),
        "concentration_chart": chart_data(concentration, frequency, "concentration"),
        "trend": reaction_trend(reaction),
    }
