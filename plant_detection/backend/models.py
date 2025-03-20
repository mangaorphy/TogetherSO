from django.db import models

class Farmer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
class Plant(models.Model):
    name = models.CharField(max_length=100)
    scientific_name = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='plants/', blank=True, null=True)  # Add an image field
    is_featured = models.BooleanField(default=False)  # New field for featured plants

    def __str__(self):
        return self.name

class Pest(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Disease(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='diseases')

    def __str__(self):
        return f"{self.name} ({self.plant.name})"

class Recommendation(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='recommendations', null=True, blank=True)
    pest = models.ForeignKey(Pest, on_delete=models.CASCADE, related_name='recommendations', null=True, blank=True)

    def __str__(self):
        return self.title