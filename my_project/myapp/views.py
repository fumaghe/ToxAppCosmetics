from django.shortcuts import render
from .models import Ingredient

def home(request):
    ingredients = Ingredient.objects.all()
    return render(request, 'myapp/home.html', {'ingredients': ingredients})

def toxicity_calculator(request):
    if request.method == 'POST':
        # Logica per gestire la richiesta POST
        pass
    return render(request, 'myapp/toxicity_calculator.html')

def certified_cosmetics(request):
    # Logica per gestire la visualizzazione dei cosmetici certificati
    return render(request, 'myapp/certified_cosmetics.html')

def dataset(request):
    ingredients = Ingredient.objects.all()
    return render(request, 'myapp/dataset.html', {'ingredients': ingredients})
