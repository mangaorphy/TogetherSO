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
from django.core.exceptions import ObjectDoesNotExist
import numpy as np
from PIL import Image
from . import CNN
from PIL import Image
from django.db.models import Count
from django.http import JsonResponse
from django.utils.timezone import now
from django.contrib import messages
from django.views.decorators.http import require_http_methods
import requests

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
def plant_detail(request, plant_id):
    plant = get_object_or_404(Plant, pk=plant_id)
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

    # Example of recent activity (adjust query as needed)
    recent_activity = Disease.objects.all().order_by('-id')[:5]  # Recent diseases detected

    context = {
        "total_farmers": total_farmers,
        "total_plants": total_plants,
        "total_diseases": total_diseases,
        "total_pests": total_pests,
        "total_recommendations": total_recommendations,
        "recent_activity": recent_activity,
    }
    return render(request, "backend/dashboard.html", context)

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

def load_disease_and_supplement_info():
    """
    Load disease and supplement information from CSV files.
    Returns:
        - transform_index_to_disease: A dictionary mapping indices to disease details.
        - supplement_info: A DataFrame containing supplement information.
    """
    # Construct full file paths
    disease_path = os.path.join(BASE_DIR, 'disease_info.csv')
    supplement_path = os.path.join(BASE_DIR, 'supplement_info.csv')

    try:
        # Load disease info
        disease_info = pd.read_csv(disease_path, encoding='cp1252')
        
        # Convert disease_info to the desired dictionary format
        transform_index_to_disease = {
            row['index']: (
                row['disease_name'], 
                row['description'], 
                row['Possible Steps'], 
                row['image_url']
            )
            for _, row in disease_info.iterrows()
        }

    except FileNotFoundError as e:
        print(f"Error: {e.filename} not found. Ensure the file is in the correct directory.")
        transform_index_to_disease = None

    try:
        # Load supplement info
        supplement_info = pd.read_csv(supplement_path, encoding='cp1252')
    except FileNotFoundError as e:
        print(f"Error: {e.filename} not found. Ensure the file is in the correct directory.")
        supplement_info = None

    return transform_index_to_disease, supplement_info

# Load disease and supplement info
transform_index_to_disease, supplement_info = load_disease_and_supplement_info()

# Example usage
if transform_index_to_disease is not None and supplement_info is not None:
    print("Disease and supplement info loaded successfully!")
else:
    print("Failed to load disease or supplement info.")

# Load the AI Model
# Global model variable
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

model = None

def load_model():
    """
    Loads the model from DigitalOcean Spaces with caching and error handling.
    """
    global model

    if model is not None:
        return model

    try:
        # DigitalOcean Spaces URL (use your actual URL)
        model_url = "https://nyc3.digitaloceanspaces.com/togetherso/plant_disease_model_1_latest.pt?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=DO00XXTGGEQWUWUEVH8H%2F20250327%2Fnyc3%2Fs3%2Faws4_request&X-Amz-Date=20250327T154845Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=cf50b8d97fbf2ce45176a9e9ea6424c25327e3e9d5c5f95945ecc4db98598dab"

        # Download the model
        logger.info("Downloading model from DigitalOcean Spaces...")
        response = requests.get(model_url, stream=True)
        response.raise_for_status()  # Raise exception for bad status codes

        # Load directly into memory without saving to disk
        model_bytes = BytesIO()
        for chunk in response.iter_content(chunk_size=8192):
            model_bytes.write(chunk)

        # Load model from bytes
        model_bytes.seek(0)
        model = CNN.CNN(39)  # Initialize with correct number of classes
        model.load_state_dict(torch.load(model_bytes, map_location=torch.device('cpu')))
        model.eval()

        logger.info("Model successfully loaded from DigitalOcean Spaces.")
        return model

    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise RuntimeError(f"Could not load model: {str(e)}")

# Initialize model when Django starts
try:
    load_model()
except Exception as e:
    logger.error(f"Initial model loading failed: {str(e)}")

# Function to make predictions
def prediction(image_path):
    """
    Predicts the disease using the AI model loaded from DigitalOcean.
    """
    global model

    try:
        # Ensure model is loaded
        if model is None:
            load_model()

        # Load and preprocess image
        image = Image.open(image_path).convert('RGB')  # Convert to RGB to handle grayscale images
        image = image.resize((224, 224))  # Resize image to match model input size
        input_data = TF.to_tensor(image)  # Convert image to tensor
        input_data = input_data.unsqueeze(0)  # Add batch dimension

        # Make prediction
        with torch.no_grad():  # Disable gradient computation for inference
            output = model(input_data)
            pred_index = output.argmax().item()  # Get the predicted class index

        return pred_index

    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise RuntimeError(f"Prediction error: {str(e)}")

def disease_detection_view(request):
    """
    Django view for handling image upload, disease prediction, and saving data to the database.
    """
    if request.method == "POST":
        form = DetectionForm(request.POST, request.FILES)
        if form.is_valid():
            # Process the uploaded image
            image = form.cleaned_data['image']
            area = form.cleaned_data['area']
            notes = form.cleaned_data['notes']

            # Save the image temporarily
            upload_dir = 'static/uploads'
            os.makedirs(upload_dir, exist_ok=True)  # Ensure directory exists
            file_path = os.path.join(upload_dir, image.name)
            with open(file_path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)

            # Perform AI-based prediction
            pred_index = prediction(file_path)
            print(f"Prediction Index: {pred_index}")  # Debugging line

            # Handle unknown or invalid predictions
            if pred_index < 0 or pred_index >= len(transform_index_to_disease):
                print(f"Invalid prediction index: {pred_index}")
                pred_index = -1  # Set to unknown index

            # Retrieve disease details
            try:
                disease_details = transform_index_to_disease[pred_index]
                if len(disease_details) < 4:  # Ensure tuple has at least 4 elements
                    raise KeyError("Disease details are incomplete")

                disease_name = disease_details[0]  # Name is at index 0
                description = disease_details[1]   # Description is at index 1
                prevention = disease_details[2]    # Prevention steps are at index 2
                image_url = disease_details[3]    # Image URL is at index 3

                # Extract plant and disease names
                plant_name, disease_name = disease_name.split(':') if ':' in disease_name else ('Unknown', 'Unknown')
                plant_name = plant_name.strip()
                disease_name = disease_name.strip()

                # Get or create corresponding objects in the database
                plant, _ = Plant.objects.get_or_create(name=plant_name, defaults={
                    'scientific_name': f'{plant_name} spp.',  # Default scientific name
                    'description': 'Healthy plant.',
                    'image': f'plants/{plant_name.lower().replace(" ", "_")}_healthy.jpg'  # Default healthy image
                })

                disease, _ = Disease.objects.get_or_create(name=disease_name, defaults={
                    'description': description,
                    'prevention_steps': prevention,
                    'plant': plant
                })

                # Create a DiseaseDetection record
                detection = DiseaseDetection.objects.create(
                    farmer=request.user if request.user.is_authenticated else None,
                    plant=plant,
                    disease=disease,
                    image=image,
                    area=area,
                    notes=notes,
                    created_at=now()
                )

                print(f"Disease Name: {disease_name}")
                print(f"Description: {description}")
                print(f"Prevention: {prevention}")
                print(f"Image URL: {image_url}")

                # Render the results
                return render(request, 'backend/disease_result.html', {
                    'title': disease_name,
                    'desc': description,
                    'prevent': prevention,
                    'image_url': image_url,
                    'detection': detection
                })
            except (KeyError, IndexError):
                # Handle unknown diseases
                disease_name = "Unknown"
                description = "The AI engine was unable to identify the disease."
                prevention = "Please consult an agricultural expert for further assistance."
                image_url = None

                # Create a generic DiseaseDetection record for unknown cases
                detection = DiseaseDetection.objects.create(
                    farmer=request.user if request.user.is_authenticated else None,
                    plant=None,
                    disease=None,
                    image=image,
                    area=area,
                    notes=notes,
                    created_at=now()
                )

                return render(request, 'backend/disease_result.html', {
                    'title': disease_name,
                    'desc': description,
                    'prevent': prevention,
                    'image_url': image_url,
                    'detection': detection
                })
    else:
        form = DetectionForm()

    return render(request, 'backend/disease_detection.html', {'form': form})

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

def market_view(request):
    """
    View to display disease-related supplements.
    """
    # return render(request, 'backend/market.html', {
    #     'supplement_image': list(supplement_info['supplement image']),
    #     'supplement_name': list(supplement_info['supplement name']),
    #     'disease': list(disease_info['disease_name']),
    #     'buy': list(supplement_info['buy link'])
    # })





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