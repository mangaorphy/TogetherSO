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

# Global model variable
model = None
MODEL_FILENAME = "plant_disease_model_1_latest.pt"
MODEL_URL = "https://nyc3.digitaloceanspaces.com/togetherso/plant_disease_model_1_latest.pt?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=DO00XXTGGEQWUWUEVH8H%2F20250405%2Fnyc3%2Fs3%2Faws4_request&X-Amz-Date=20250405T085611Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=7b49b14618306166741933dd5a595ae012de30d9ac0a5da87cce2935f9b6ca91"

def load_model():
    """
    Loads the model with local file fallback and proper resource cleanup.
    """
    global model
    
    if model is not None:
        return model

    model_path = os.path.join(os.path.dirname(__file__), MODEL_FILENAME)
    
    try:
        # Try loading from local file first
        if os.path.exists(model_path):
            logger.info(f"Loading model from local file: {model_path}")
            model = CNN.CNN(39)
            model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
            model.eval()
            return model
        
        # Download if local file doesn't exist
        logger.info("Downloading model from DigitalOcean Spaces...")
        response = requests.get(MODEL_URL, stream=True, timeout=60)
        response.raise_for_status()

        # Use context managers to ensure proper resource cleanup
        with BytesIO() as model_bytes:
            for chunk in response.iter_content(chunk_size=8192):
                model_bytes.write(chunk)
            
            model_bytes.seek(0)
            
            # Load model
            model = CNN.CNN(39)
            model.load_state_dict(torch.load(model_bytes, map_location=torch.device('cpu')))
            model.eval()
            
            # Save to local file for future use
            try:
                torch.save(model.state_dict(), model_path)
                logger.info(f"Model saved locally at: {model_path}")
            except Exception as save_error:
                logger.warning(f"Could not save model locally: {save_error}")
            
            return model

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error downloading model: {str(e)}")
        raise RuntimeError("Could not download model. Check your internet connection.")
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        model = None
        raise RuntimeError(f"Model loading failed: {str(e)}")

def prediction(image_path):
    """
    Predicts plant disease from an image with proper resource handling.
    """
    try:
        # Ensure model is loaded
        if model is None:
            load_model()

        # Load and preprocess image with context manager
        with Image.open(image_path) as img:
            image = img.convert('RGB').resize((224, 224))
            input_data = TF.to_tensor(image).unsqueeze(0)

        # Make prediction
        with torch.no_grad():
            output = model(input_data)
            pred_index = output.argmax().item()

        return pred_index

    except FileNotFoundError:
        logger.error(f"Image file not found: {image_path}")
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise RuntimeError(f"Prediction error: {str(e)}")
def disease_detection_view(request):
    """
    Django view for handling image upload, disease prediction, and saving data to the database.
    """
    # Define default values for unknown cases
    healthy_indices = [3, 5, 7, 11, 15, 18, 20, 23, 24, 25, 28, 38]

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

            try:
                # Retrieve disease details
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
                    'detection': detection,
                    'healthy_indices': healthy_indices,  # Pass the list of healthy indices
                    'pred': pred_index,  # Pass the prediction index for conditional rendering
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
                    'detection': detection,
                    'healthy_indices': [],  # Empty list for unknown cases
                    'pred': pred_index,  # Pass the prediction index for conditional rendering
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