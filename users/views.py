from django.contrib.auth import (
    authenticate,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import get_object_or_404, redirect, render

from team_finder.utils import get_page
from users.constants import (
    FILTER_FAVORITE_OWNERS,
    FILTER_INTERESTED_USERS,
    FILTER_MY_PARTICIPANTS,
    FILTER_PARTICIPATING_OWNERS,
    PARTICIPANTS_PER_PAGE,
)
from users.forms import LoginForm, ProfileForm, RegistrationForm
from users.models import User


def register(request):
    form = RegistrationForm(request.POST or None)
    if not form.is_valid():
        return render(request, "users/register.html", {"form": form})
    user = form.save()
    login(request, user)
    return redirect("projects:list")


def login_view(request):
    form = LoginForm(request.POST or None)
    if not form.is_valid():
        return render(request, "users/login.html", {"form": form})
    user = authenticate(
        request,
        email=form.cleaned_data["email"],
        password=form.cleaned_data["password"],
    )
    if user is None:
        form.add_error(None, "Неверный имейл или пароль")
        return render(request, "users/login.html", {"form": form})
    login(request, user)
    return redirect("projects:list")


def logout_view(request):
    logout(request)
    return redirect("projects:list")


@login_required
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if not form.is_valid():
        return render(request, "users/change_password.html", {"form": form})
    user = form.save()
    update_session_auth_hash(request, user)
    return redirect("users:detail", user_id=request.user.id)


def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, "users/user-details.html", {"user": user})


def participants(request):
    users = User.objects.all()
    active_filter = ""
    if request.user.is_authenticated:
        active_filter = request.GET.get("filter", "")
    if active_filter == FILTER_FAVORITE_OWNERS:
        users = users.filter(owned_projects__interested_users=request.user)
    elif active_filter == FILTER_PARTICIPATING_OWNERS:
        users = users.filter(owned_projects__participants=request.user)
    elif active_filter == FILTER_INTERESTED_USERS:
        users = users.filter(favorites__owner=request.user)
    elif active_filter == FILTER_MY_PARTICIPANTS:
        users = users.filter(participated_projects__owner=request.user)
    users = users.distinct().order_by("id")
    return render(
        request,
        "users/participants.html",
        {
            "participants": users,
            "page_obj": get_page(request, users, PARTICIPANTS_PER_PAGE),
            "active_filter": active_filter,
            "query_prefix": (
                f"filter={active_filter}&" if active_filter else ""
            ),
        },
    )


@login_required
def edit_profile(request):
    form = ProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user,
    )
    if not form.is_valid():
        return render(request, "users/edit_profile.html", {"form": form})
    form.save()
    return redirect("users:detail", user_id=request.user.id)
