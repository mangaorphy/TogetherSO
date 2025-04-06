# backend/admin.py

from django.contrib import admin
from .models import Farmer, Plant, Pest, Disease, DiseaseDetection, Recommendation, NewsUpdate, ContactMessage, Page

# Register models
@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'address')
    search_fields = ('name', 'email')
@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ('name', 'scientific_name', 'is_featured')
    list_filter = ('is_featured',)
    search_fields = ('name', 'scientific_name')
    ordering = ('name',)
    fields = ('name', 'scientific_name', 'description', 'image', 'is_featured')

    def save_model(self, request, obj, form, change):
        """
        Ensure the image is saved correctly.
        """
        super().save_model(request, obj, form, change)
        print(f"Image saved successfully at: {obj.image.path}")  # Debugging line

@admin.register(Pest)
class PestAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'plant', 'description', 'prevention_steps')
    search_fields = ('name', 'plant__name')
    list_filter = ('plant',)

@admin.register(DiseaseDetection)
class DiseaseDetectionAdmin(admin.ModelAdmin):
    list_display = ('farmer', 'plant', 'disease', 'area', 'notes', 'created_at')
    search_fields = ('farmer__username', 'plant__name', 'disease__name', 'area')
    list_filter = ('created_at', 'area', 'plant', 'disease')
    date_hierarchy = 'created_at'

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('title', 'disease', 'pest')
    search_fields = ('title', 'disease__name', 'pest__name')
    list_filter = ('disease', 'pest')

@admin.register(NewsUpdate)
class NewsUpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'disease', 'created_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at', 'disease')
    date_hierarchy = 'created_at'

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'subject')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'image_url', 'action_text')
    search_fields = ('title', 'content')
    list_filter = ('title',)