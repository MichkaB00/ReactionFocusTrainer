import json
from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST, require_safe
from django.views.generic import ListView
from pymongo.errors import DuplicateKeyError, PyMongoError

from .models import TrainingMode
from .mongo import get_collection
from .analytics import PERIODS, analyze_results, period_bounds


class TrainingModeListView(ListView):
    model = TrainingMode
    template_name = "training/home.html"
    context_object_name = "modes"
    queryset = TrainingMode.objects.filter(is_active=True)


@login_required
@require_safe
def reaction(request):
    mode = get_object_or_404(TrainingMode, slug="reaction", is_active=True)
    return render(request, "training/reaction.html", {"mode": mode})


@login_required
@require_safe
def concentration(request):
    mode = get_object_or_404(TrainingMode, slug="concentration", is_active=True)
    return render(request, "training/concentration.html", {"mode": mode})


@login_required
@require_safe
def statistics(request):
    period = request.GET.get("period", "week")
    if period not in PERIODS:
        period = "week"
    now = timezone.now()
    previous_start, _, _ = period_bounds(period, now)
    context = {"period": period, "periods": PERIODS, "statistics_error": False}
    try:
        documents = list(get_collection().find({
            "user_id": request.user.id,
            "created_at": {
                "$gte": previous_start, "$lte": now,
            },
        }, {"_id": 0, "mode": 1, "created_at": 1, "reaction_time_ms": 1,
            "correct_answers": 1, "wrong_answers": 1, "missed_signals": 1}))
    except PyMongoError:
        context["statistics_error"] = True
    else:
        context.update(analyze_results(documents, period, now))
    return render(request, "training/statistics.html", context)


@login_required
@require_POST
def save_result(request):
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError
        attempt = UUID(data["attempt_id"])
        if attempt.version != 4:
            raise ValueError
        attempt_id = str(attempt)
        mode = data["mode"]
        if mode == "reaction":
            reaction_time = data["reaction_time_ms"]
            if type(reaction_time) is not int or not 1 <= reaction_time <= 60000:
                raise ValueError
            result = {"reaction_time_ms": reaction_time}
        elif mode == "concentration":
            fields = ("correct_answers", "wrong_answers", "missed_signals")
            result = {field: data[field] for field in fields}
            if any(type(value) is not int or not 0 <= value <= 10 for value in result.values()):
                raise ValueError
            if sum(result.values()) != 10 or result["wrong_answers"] > 5 or result["missed_signals"] > 5:
                raise ValueError
        else:
            raise ValueError
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        return JsonResponse({"error": "Некоректний результат тренування."}, status=400)

    if not TrainingMode.objects.filter(slug=mode, is_active=True).exists():
        return JsonResponse({"error": "Режим тренування недоступний."}, status=400)

    document = {
        "user_id": request.user.id,
        "mode": mode,
        "created_at": timezone.now(),
        "attempt_id": attempt_id,
        **result,
    }
    try:
        collection = get_collection()
        collection.create_index("attempt_id", unique=True, sparse=True)
        try:
            collection.insert_one(document)
        except DuplicateKeyError:
            existing = collection.find_one({"attempt_id": attempt_id})
            if not existing or any(existing.get(key) != value for key, value in {
                "user_id": request.user.id, "mode": mode, **result,
            }.items()):
                return JsonResponse({"error": "Результат уже існує."}, status=409)
    except PyMongoError:
        return JsonResponse({"error": "Не вдалося зберегти результат."}, status=503)
    return JsonResponse({"saved": True})
