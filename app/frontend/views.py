from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView
from api.forms import UserRegistrationForm, UserUpdateForm
from api.models import (
    Organization, 
    )

# === Вход ===
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Добро пожаловать, {user.get_full_name() or user.username}!")
            return redirect("home")  # перенаправление на главную
        else:
            messages.error(request, "Неверное имя пользователя или пароль.")
    return render(request, "auth/login.html")


# === Выход ===
def logout_view(request):
    logout(request)
    messages.info(request, "Вы вышли из системы.")
    return redirect("login")


# === Регистрация (опционально — только для админов или внутреннего использования) ===
def register_view(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.role == 'admin':
        messages.error(request, "У вас нет прав на регистрацию пользователей.")
        return redirect("home")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            messages.success(request, f"Пользователь {user.username} успешно создан.")
            return redirect("register")
    else:
        form = UserRegistrationForm()

    return render(request, "auth/register.html", {"form": form})


# === Главная страница (после входа) ===
@login_required
def home_view(request):
    return render(request, "home.html")


def organizations(request):
    organizations = Organization.objects.all()
    return render(request, 'frontend/organizations.html', {'organizations': organizations})