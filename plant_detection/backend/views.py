import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Farmer, Plant, Pest, Disease, Recommendation,DiseaseDetection, NewsUpdate, Page
from .forms import DetectionForm, ContactForm
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import torch
import torchvision.transforms.functional as TF
import torch.nn.functional as F
from django.core.exceptions import ObjectDoesNotExist
import numpy as np
from PIL import Image, UnidentifiedImageError
from . import CNN
from PIL import Image
from django.db.models import Count
from django.http import JsonResponse
from django.utils.timezone import now
from django.contrib import messages
from django.views.decorators.http import require_http_methods
import requests
from django.conf import settings

# Authentication views


# def register(request):
#     if request.method == "POST":
#         username = request.POST["username"]
#         email = request.POST["email"]
#         password = request.POST["password"]
#         confirm_password = request.POST["confirm_password"]

#         if password != confirm_password:
#             return render(request, "backend/register.html", {"error": "Passwords do not match"})
        
#         if User.objects.filter(username=username).exists():
#             return render(request, "backend/register.html", {"error": "Username already taken"})

#         user = User.objects.create_user(username=username, email=email, password=password)
#         login(request, user)
#         return redirect("home")

#     return render(request, "backend/register.html")

@require_http_methods(["GET", "POST"])
@login_required
def custom_logout(request):
    if request.method == 'POST':
        logout(request)
        request.session.flush()  # Clears all session data
        return redirect('login')
    
    # For GET requests, show confirmation page
    return render(request, 'backend/logout.html')

# Home views
@login_required
def home(request):
    # Fetch up to 3 featured plants randomly
    featured_plants = Plant.objects.filter(is_featured=True).order_by('?')[:3]
    return render(request, 'backend/home.html', {'featured_plants': featured_plants})

# Plant detail
import logging

logger = logging.getLogger(__name__)

def plant_detail(request, plant_id):
    plant = get_object_or_404(Plant, pk=plant_id)
    logger.info(f"Image URL for {plant.name}: {plant.image.url}")
    return render(request, 'backend/plant_detail.html', {'plant': plant})

#  About views
@login_required
def services(request):
    return render(request, 'backend/services.html')

@login_required
def dashboard(request):
    # Aggregate data for the dashboard
    total_farmers = Farmer.objects.count()
    total_plants = Plant.objects.count()
    total_diseases = Disease.objects.count()
    total_pests = Pest.objects.count()
    total_recommendations = Recommendation.objects.count()

    # Fetch recent recommendations
    recent_recommendations = Recommendation.objects.all().order_by('-id')[:5]

    # Fetch recent disease detections (adjust query as needed)
    recent_activity = DiseaseDetection.objects.select_related('disease', 'disease__plant').order_by('-created_at')[:5]

    context = {
        "total_farmers": total_farmers,
        "total_plants": total_plants,
        "total_diseases": total_diseases,
        "total_pests": total_pests,
        "total_recommendations": total_recommendations,
        "recent_recommendations": recent_recommendations,
        "recent_activity": recent_activity,
    }
    return render(request, "backend/dashboard.html", context)

from django.views.generic import DetailView

class RecommendationDetailView(DetailView):
    model = Recommendation
    template_name = 'backend/recommendation_detail.html'
    context_object_name = 'recommendation'

def contact_us_view(request):
    """
    Django view for handling contact form submissions.
    """
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been sent successfully!")
            return redirect('contact-us')
    else:
        form = ContactForm()

    return render(request, 'backend/contact_us.html', {'form': form})

#  Page views for footer links
# def page_detail(request, slug):
#     page = get_object_or_404(Page, slug=slug)
#     return render(request, 'backend/page_detail.html', {'page': page})

def page_detail(request, slug):
    """
    Django view for rendering dynamic pages.
    """
    page = get_object_or_404(Page, title__iexact=slug.replace('-', ' '))
    context = {
        'page': page,
    }
    return render(request, 'backend/page_detail.html', context)

# < --------------------------------------------------------------------------------------------- >
# Load CSV files (adjust paths if needed)
import pandas as pd
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

disease_path = os.path.join(BASE_DIR, 'disease_info.csv')
supplement_path = os.path.join(BASE_DIR, 'supplement_info.csv')

disease_info = pd.read_csv(disease_path , encoding='cp1252')
supplement_info = pd.read_csv(supplement_path, encoding='cp1252')

import os

# Define the absolute path to the model file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "plant_disease_model_1_latest.pt")

# Load the model
model = CNN.CNN(39)
model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))
model.eval()

def prediction(image_path):
    image = Image.open(image_path)
    image = image.resize((224, 224))
    input_data = TF.to_tensor(image)
    input_data = input_data.view((-1, 3, 224, 224))
    output = model(input_data)
    output = output.detach().numpy()
    index = np.argmax(output)
    return index
        
def disease_detection_view(request):
    if request.method == 'POST':
        # Use request.FILES instead of request.files
        if 'image' not in request.FILES:
            return render(request, 'backend/disease_detection.html', {
                'error': 'No image file was uploaded'
            })
            
        image = request.FILES['image']
        filename = image.name  # Use .name instead of .filename
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        
        # Save the uploaded file properly
        with open(file_path, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)
        
        print(file_path)
        
        try:
            pred = prediction(file_path)
            title = disease_info['disease_name'][pred]
            description = disease_info['description'][pred]
            prevent = disease_info['Possible Steps'][pred]
            image_url = disease_info['image_url'][pred]
            supplement_name = supplement_info['supplement name'][pred]
            supplement_image_url = supplement_info['supplement image'][pred]
            supplement_buy_link = supplement_info['buy link'][pred]
            
            return render(request, 'backend/disease_detection.html', {
                'title': title,
                'desc': description,
                'prevent': prevent,
                'image_url': image_url,
                'pred': pred,
                'sname': supplement_name,
                'simage': supplement_image_url,
                'buy_link': supplement_buy_link,
                'healthy_indices': [3, 5, 7, 11, 15, 18, 20, 23, 24, 25, 28, 38]  # Add healthy indices
            })
            
        except Exception as e:
            print(f"Error during prediction: {str(e)}")
            return render(request, 'backend/disease_detection.html', {
                'error': 'Error processing the image'
            })

    # Handle GET requests or other methods
    return render(request, 'backend/disease_detection.html')

# Trending Diseases API
def trending_diseases_api(request):
    """
    Returns JSON data of the top 5 trending diseases in a specific area.
    """
    # Get query parameters
    area = request.GET.get('area', 'default_area')  # Default to 'default_area'
    start_date = request.GET.get('start_date', None)  # Optional: Filter by date range
    end_date = request.GET.get('end_date', None)

    # Filter detections by area and date range
    queryset = DiseaseDetection.objects.filter(area=area)
    if start_date and end_date:
        queryset = queryset.filter(created_at__range=[start_date, end_date])

    # Aggregate data by disease
    trending = (
        queryset.values('disease__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]  # Top 5 trending diseases
    )

    # Convert to list for JSON response
    data = [{'disease_name': d['disease__name'], 'count': d['count']} for d in trending]

    # Handle empty data gracefully
    if not data:
        data = [{'disease_name': 'No Data', 'count': 0}]

    return JsonResponse(data, safe=False)

def news_view(request):
    """
    Django view for displaying news updates.
    """
    news_updates = NewsUpdate.objects.all()[:10]  # Fetch the latest 10 updates
    context = {
        'news_updates': news_updates,
    }
    return render(request, 'backend/news.html', context)
# Market view
@login_required
def market_view(request):
    """
    Django view for displaying disease-related supplements.
    """
    # Load supplement information from CSV
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    supplement_path = os.path.join(BASE_DIR, 'supplement_info.csv')

    try:
        supplement_info = pd.read_csv(supplement_path, encoding='cp1252')
        # Convert DataFrame to a list of dictionaries for easier iteration in templates
        supplements = [
            {
                'disease_name': row['disease_name'],
                'supplement_name': row['supplement name'],
                'supplement_image': row['supplement image'],
                'buy_link': row['buy link']
            }
            for _, row in supplement_info.iterrows()
        ]
    except FileNotFoundError as e:
        print(f"Error: {e.filename} not found. Ensure the file is in the correct directory.")
        supplements = []

    return render(request, 'backend/market.html', {'supplements': supplements})





# Farmer Views
class FarmerListView(ListView):
    model = Farmer
    template_name = 'backend/farmer_list.html'
    context_object_name = 'farmers'

class FarmerDetailView(DetailView):
    model = Farmer
    template_name = 'backend/farmer_detail.html'
    context_object_name = 'farmer'

class FarmerCreateView(CreateView):
    model = Farmer
    fields = ['name', 'email', 'phone', 'address']
    template_name = 'backend/farmer_form.html'
    success_url = reverse_lazy('farmer-list')

class FarmerUpdateView(UpdateView):
    model = Farmer
    fields = ['name', 'email', 'phone', 'address']
    template_name = 'backend/farmer_form.html'
    success_url = reverse_lazy('farmer-list')

class FarmerDeleteView(DeleteView):
    model = Farmer
    template_name = 'backend/farmer_confirm_delete.html'
    success_url = reverse_lazy('farmer-list')

# Plant Views
class PlantListView(ListView):
    model = Plant
    template_name = 'backend/plant_list.html'
    context_object_name = 'plants'

class PlantDetailView(DetailView):
    model = Plant
    template_name = 'backend/plant_detail.html'
    context_object_name = 'plant'

class PlantCreateView(CreateView):
    model = Plant
    fields = ['name', 'scientific_name', 'description']
    template_name = 'backend/plant_form.html'
    success_url = reverse_lazy('plant-list')

class PlantUpdateView(UpdateView):
    model = Plant
    fields = ['name', 'scientific_name', 'description']
    template_name = 'backend/plant_form.html'
    success_url = reverse_lazy('plant-list')

class PlantDeleteView(DeleteView):
    model = Plant
    template_name = 'backend/plant_confirm_delete.html'
    success_url = reverse_lazy('plant-list')

# Disease Views
class DiseaseListView(ListView):
    model = Disease
    template_name = 'backend/disease_list.html'
    context_object_name = 'diseases'

class DiseaseDetailView(DetailView):
    model = Disease
    template_name = 'backend/disease_detail.html'
    context_object_name = 'disease'

class DiseaseCreateView(CreateView):
    model = Disease
    fields = ['name', 'description', 'plant']
    template_name = 'backend/disease_form.html'
    success_url = reverse_lazy('disease-list')

class DiseaseUpdateView(UpdateView):
    model = Disease
    fields = ['name', 'description', 'plant']
    template_name = 'backend/disease_form.html'
    success_url = reverse_lazy('disease-list')

class DiseaseDeleteView(DeleteView):
    model = Disease
    template_name = 'backend/disease_confirm_delete.html'
    success_url = reverse_lazy('disease-list')

# Pest Views
class PestListView(ListView):
    model = Pest
    template_name = 'backend/pest_list.html'
    context_object_name = 'pests'

class PestDetailView(DetailView):
    model = Pest
    template_name = 'backend/pest_detail.html'
    context_object_name = 'pest'

class PestCreateView(CreateView):
    model = Pest
    fields = ['name', 'description']
    template_name = 'backend/pest_form.html'
    success_url = reverse_lazy('pest-list')

class PestUpdateView(UpdateView):
    model = Pest
    fields = ['name', 'description']
    template_name = 'backend/pest_form.html'
    success_url = reverse_lazy('pest-list')

class PestDeleteView(DeleteView):
    model = Pest
    template_name = 'backend/pest_confirm_delete.html'
    success_url = reverse_lazy('pest-list')

# Recommendation Views
class RecommendationListView(ListView):
    model = Recommendation
    template_name = 'backend/recommendation_list.html'
    context_object_name = 'recommendations'

class RecommendationDetailView(DetailView):
    model = Recommendation
    template_name = 'backend/recommendation_detail.html'
    context_object_name = 'recommendation'

class RecommendationCreateView(CreateView):
    model = Recommendation
    fields = ['title', 'content', 'disease', 'pest']
    template_name = 'backend/recommendation_form.html'
    success_url = reverse_lazy('recommendation-list')

class RecommendationUpdateView(UpdateView):
    model = Recommendation
    fields = ['title', 'content', 'disease', 'pest']
    template_name = 'backend/recommendation_form.html'
    success_url = reverse_lazy('recommendation-list')

class RecommendationDeleteView(DeleteView):
    model = Recommendation
    template_name = 'backend/recommendation_confirm_delete.html'
    success_url = reverse_lazy('recommendation-list')
# < --------------------------------------------------------------------------------------------- >