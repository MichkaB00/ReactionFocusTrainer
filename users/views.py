from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from pymongo.errors import PyMongoError

from training.models import TrainingMode
from training.mongo import get_collection
from .forms import ProfileForm, RegistrationForm


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("users:profile")
    form = RegistrationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("users:profile")
    return render(request, "users/register.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def profile(request):
    form = ProfileForm(
        request.POST if request.method == "POST" else None, instance=request.user
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Ім’я та прізвище збережено.")
        return redirect("users:profile")
    try:
        history = list(get_collection().find({"user_id": request.user.id}).sort(
            [("created_at", -1), ("_id", -1)]
        ).limit(10))
        history_error = False
    except PyMongoError:
        history = []
        history_error = True
    return render(request, "users/profile.html", {
        "form": form,
        "modes": TrainingMode.objects.filter(is_active=True),
        "history": history,
        "history_error": history_error,
    })
