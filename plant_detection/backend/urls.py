from django.conf import settings
from django.urls import path
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    # Authentication URLs for the login, creating an account, and logging out
    path("login/", views.custom_login_view, name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),

    # Home Page
    path('home/', views.home, name='home'),
    path('plants/<int:plant_id>/', views.plant_detail, name='plant-detail'),

    # Dashboard Page
    path('dashboard/', views.dashboard, name='dashboard'),

    # About Page
    path('services/', views.services, name='services'),

    # AI-based plant disease detection
    path('submit', views.disease_detection_view, name='submit'),
    path('market/', views.market_view, name='market'),

    # Farmer URLs
    path('farmers/', views.FarmerListView.as_view(), name='farmer-list'),
    path('farmers/<int:pk>/', views.FarmerDetailView.as_view(), name='farmer-detail'),
    path('farmers/create/', views.FarmerCreateView.as_view(), name='farmer-create'),
    path('farmers/<int:pk>/update/', views.FarmerUpdateView.as_view(), name='farmer-update'),
    path('farmers/<int:pk>/delete/', views.FarmerDeleteView.as_view(), name='farmer-delete'),

    # Plant URLs
    path('plants/', views.PlantListView.as_view(), name='plant-list'),
    path('plants/<int:pk>/', views.PlantDetailView.as_view(), name='plant-detail'),
    path('plants/create/', views.PlantCreateView.as_view(), name='plant-create'),
    path('plants/<int:pk>/update/', views.PlantUpdateView.as_view(), name='plant-update'),
    path('plants/<int:pk>/delete/', views.PlantDeleteView.as_view(), name='plant-delete'),

    # Disease URLs
    path('diseases/', views.DiseaseListView.as_view(), name='disease-list'),
    path('diseases/<int:pk>/', views.DiseaseDetailView.as_view(), name='disease-detail'),
    path('diseases/create/', views.DiseaseCreateView.as_view(), name='disease-create'),
    path('diseases/<int:pk>/update/', views.DiseaseUpdateView.as_view(), name='disease-update'),
    path('diseases/<int:pk>/delete/', views.DiseaseDeleteView.as_view(), name='disease-delete'),

    # Pest URLs
    path('pests/', views.PestListView.as_view(), name='pest-list'),
    path('pests/<int:pk>/', views.PestDetailView.as_view(), name='pest-detail'),
    path('pests/create/', views.PestCreateView.as_view(), name='pest-create'),
    path('pests/<int:pk>/update/', views.PestUpdateView.as_view(), name='pest-update'),
    path('pests/<int:pk>/delete/', views.PestDeleteView.as_view(), name='pest-delete'),

    # Recommendation URLs
    path('recommendations/', views.RecommendationListView.as_view(), name='recommendation-list'),
    path('recommendations/<int:pk>/', views.RecommendationDetailView.as_view(), name='recommendation-detail'),
    path('recommendations/create/', views.RecommendationCreateView.as_view(), name='recommendation-create'),
    path('recommendations/<int:pk>/update/', views.RecommendationUpdateView.as_view(), name='recommendation-update'),
    path('recommendations/<int:pk>/delete/', views.RecommendationDeleteView.as_view(), name='recommendation-delete'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])