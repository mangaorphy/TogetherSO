from django.core.files.storage import default_storage 
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.contrib.auth.models import User 
import logging

class Farmer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    
logger = logging.getLogger(__name__)
class Plant(models.Model):
    name = models.CharField(max_length=100)
    scientific_name = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(
        upload_to='plants/', 
        storage=default_storage,  # This ensures Spaces is used
        blank=True, 
        null=True
    )  # Add an image field
    is_featured = models.BooleanField(default=False)  # New field for featured plants

    def save(self, *args, **kwargs):
        """
        Overrides the save method to log image upload details.
        """
        super().save(*args, **kwargs)
        if self.image:
            logger.info(f"Image saved successfully for {self.name} at: {self.image.url}")

    def __str__(self):
        return self.name

    @property
    def image_url(self):
        """
        Returns the image URL or a fallback if the image is missing.
        """
        try:
            return self.image.url
        except ValueError:
            return "{% static 'images/default_plant.jpg' %}"  # Fallback image

class Pest(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Disease(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    prevention_steps = models.TextField(blank=True, null=True)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='diseases')

    def __str__(self):
        return f"{self.name} ({self.plant.name})"
    
class DiseaseDetection(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='detections', null=True, blank=True)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='detections')
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='detections', null=True, blank=True)
    image = models.ImageField(upload_to='detections/', blank=True, null=True)
    area = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.disease.name} detected in {self.plant.name} ({self.created_at.strftime('%Y-%m-%d')})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Disease Detection"
        verbose_name_plural = "Disease Detections"

class Recommendation(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='recommendations', null=True, blank=True)
    pest = models.ForeignKey(Pest, on_delete=models.CASCADE, related_name='recommendations', null=True, blank=True)

    def __str__(self):
        return self.title
    
class NewsUpdate(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    disease = models.ForeignKey('Disease', on_delete=models.CASCADE, related_name='news_updates', null=True, blank=True)
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
        verbose_name = "News Update"
        verbose_name_plural = "News Updates"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.name} - {self.subject}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

class Page(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image_url = models.URLField(blank=True, null=True)  # Optional image URL
    action_link = models.URLField(blank=True, null=True)  # Optional action link
    action_text = models.CharField(max_length=100, blank=True, null=True)  # Optional action button text

    def __str__(self):
        return self.title