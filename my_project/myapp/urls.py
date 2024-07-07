from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('toxicity_calculator/', views.toxicity_calculator, name='toxicity_calculator'),
    path('certified_cosmetics/', views.certified_cosmetics, name='certified_cosmetics'),
    path('dataset/', views.dataset, name='dataset'),
]
