from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegisterUserForm


def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('jdm-index')

        else:
            messages.success(request, ("Erreur... Dommage, il faudra recommencer !"))
            return redirect('login')

    else:
        return render(request, 'authenticate/login.html', {})


def logout_user(request):
    logout(request)
    messages.success(request, ("Vous êtes déconnecté.e"))
    return redirect('jdm-index')


def register_user(request):
    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, ('Votre inscription fut un véritable succès, félicitations !'))
            return redirect('jdm-index')
        else:
            print(form.cleaned_data)
            messages.success(request, ('Il semblerait que vous n\'ayez pas correctement rempli le formulaire A38...'))
    else:
        form = RegisterUserForm()
    return render(request, 'authenticate/register_user.html', {'form': form})