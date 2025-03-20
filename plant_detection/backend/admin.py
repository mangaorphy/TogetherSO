from django.contrib import admin

from .models import Disease, Farmer, Pest, Plant, Recommendation

# Register your models here.
admin.site.register(Farmer),
@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ('name', 'scientific_name', 'is_featured')
    list_filter = ('is_featured',)
    search_fields = ('name', 'scientific_name'),
admin.site.register(Pest),
admin.site.register(Disease),
admin.site.register(Recommendation),

