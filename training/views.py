from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_safe
from django.views.generic import ListView

from .models import TrainingMode


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
