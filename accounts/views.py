from django.shortcuts import render

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.views import View
from django.views.generic import  CreateView
from . forms import UserCreateForm, LoginForm
from django.urls import reverse_lazy

class CreateAccountView(CreateView):
    ''' Create new account'''
    def post(self, request, *args, **kwargs):
        form = UserCreateForm(data=request.POST)
        if form.is_valid():
            form.save()
            #フォームから'username'を読み取る
            username = form.cleaned_data.get('username')
            #フォームから'password1'を読み取る
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect(reverse_lazy('registration:targets'))
        return render(request, 'accounts/create.html', {'form': form,})

    def get(self, request, *args, **kwargs):
        form = UserCreateForm(request.POST)
        return  render(request, 'accounts/create.html', {'form': form,})

# create_account = Create_account.as_view()


class LoginView(View):
    ''' Process Login '''
    def post(self, request, *arg, **kwargs):
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            user = User.objects.get(username=username)
            login(request, user)
            return redirect(reverse_lazy('registration:targets'))
        return render(request, 'accounts/login.html', {'form': form,})

    def get(self, request, *args, **kwargs):
        form = LoginForm(request.POST)
        return render(request, 'accounts/login.html', {'form': form,})

# account_login = Account_login.as_view()
