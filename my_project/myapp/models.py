from django.db import models

class Ingredient(models.Model):
    pcpc_ingredientid = models.CharField(max_length=100, primary_key=True)
    pcpc_ingredientname = models.CharField(max_length=255)
    NOAEL_CIR = models.JSONField()
    LD50_CIR = models.JSONField()
    LD50_PubChem = models.JSONField()
    value_updated = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.pcpc_ingredientname
