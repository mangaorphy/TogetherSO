import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Farmer, Plant, Pest, Disease, Recommendation
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import torch
import torchvision.transforms.functional as TF
import numpy as np
from PIL import Image
from . import CNN
from PIL import Image

# Authentication views

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        if password != confirm_password:
            return render(request, "backend/register.html", {"error": "Passwords do not match"})
        
        if User.objects.filter(username=username).exists():
            return render(request, "backend/register.html", {"error": "Username already taken"})

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect("home")

    return render(request, "backend/register.html")

def custom_login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")  # Redirect to home after login
        else:
            return render(request, "backend/login.html", {"error": "Invalid credentials"})

    return render(request, "backend/login.html")

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


# < --------------------------------------------------------------------------------------------- >
# Load CSV files (adjust paths if needed)
import pandas as pd
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
disease_path = os.path.join(BASE_DIR, 'disease_info.csv')
supplement_path = os.path.join(BASE_DIR, 'supplement_info.csv')

try:
    disease_info = pd.read_csv(disease_path, encoding='cp1252')
    supplement_info = pd.read_csv(supplement_path, encoding='cp1252')
except FileNotFoundError:
    print("Error: 'supplement_info.csv' not found. Ensure the file is in the correct directory.")
    supplement_info = None  # Or handle it accordingly
    print("Error: 'disease_info.csv' not found. Ensure the file is in the correct directory.")
    disease_info = None  # Or handle it accordingly

# Load the AI Model
model = CNN.CNN(39)
model_path = os.path.join(BASE_DIR, "plant_disease_model_1_latest.pt")
model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
model.eval()

# Function to make predictions
def prediction(image_path):
    """
    Function to load an image, process it, and predict the disease using the AI model.
    """
    image = Image.open(image_path)
    image = image.resize((224, 224))
    input_data = TF.to_tensor(image)
    input_data = input_data.view((-1, 3, 224, 224))
    output = model(input_data)
    output = output.detach().numpy()
    index = np.argmax(output)
    return index

def disease_detection_view(request):
    """
    Django view for handling image upload and disease prediction.
    """
    if request.method == "POST":
        # Get the uploaded image
        image = request.FILES['image']
        
        # Save the image to the 'static/uploads' directory
        upload_dir = 'static/uploads'
        os.makedirs(upload_dir, exist_ok=True)  # Create the directory if it doesn't exist
        file_path = os.path.join(upload_dir, image.name)
        with open(file_path, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)
        
        # Make a prediction
        pred_index = prediction(file_path)
        
        # Retrieve disease details
        title = disease_info['disease_name'][pred_index]
        description = disease_info['description'][pred_index]
        prevent = disease_info['Possible Steps'][pred_index]
        image_url = disease_info['image_url'][pred_index]
        supplement_name = supplement_info['supplement name'][pred_index]
        supplement_image_url = supplement_info['supplement image'][pred_index]
        supplement_buy_link = supplement_info['buy link'][pred_index]

        print(f"Prediction Index: {pred_index}")
        print(f"Title: {title}")
        print(f"Description: {description}")
        print(f"Image URL: {image_url}")

        # Render the results
        return render(request, 'backend/disease_result.html', {
            'title': title,
            'desc': description,
            'prevent': prevent,
            'image_url': image_url,
            'pred': pred_index,
            'sname': supplement_name,
            'simage': supplement_image_url,
            'buy_link': supplement_buy_link,
        })

    return render(request, 'backend/disease_detection.html')

def market_view(request):
    """
    View to display disease-related supplements.
    """
    return render(request, 'backend/market.html', {
        'supplement_image': list(supplement_info['supplement image']),
        'supplement_name': list(supplement_info['supplement name']),
        'disease': list(disease_info['disease_name']),
        'buy': list(supplement_info['buy link'])
    })





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