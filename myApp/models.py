from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class TableCategory(models.Model):
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Table(models.Model):
    
    status_choice = (
        ("vecant", "vecant"),
        ("occupied", "occupied"),
        ("reserved", "reserved")
    )
    name = models.CharField(max_length=100)
    capicity = models.PositiveBigIntegerField()
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(TableCategory, on_delete=models.CASCADE)
    status = models.CharField(max_length=100, choices=status_choice, default="vecant")

    def __str__(self):
        return self.name


class MenuCategory(models.Model):
    
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE)

    
    def __str__(self):
        return self.name
    

class Bill(models.Model):
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True) # Link to the table if it exists
    table_name = models.CharField(max_length=100) # Store the table name as it was on the bill
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True, blank=True) # Link to menu item
    # item_name = models.CharField(max_length=100) # Store name at time of sale
    # quantity = models.PositiveIntegerField()
    # price = models.DecimalField(max_digits=7, decimal_places=2) # Store price at time of sale

    def __str__(self):
        return f"Bill {self.id} for {self.table_name} at {self.created_at.strftime('%Y-%m-%d')}"

class BillItem(models.Model):
    bill = models.ForeignKey(Bill, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True, blank=True) # Link to menu item
    item_name = models.CharField(max_length=100) # Store name at time of sale
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=7, decimal_places=2) # Store price at time of sale

    def __str__(self):
        return f"{self.quantity} x {self.item_name}"
  
    
class Kot(models.Model):
    # MODIFY THIS LINE
    kot_id = models.PositiveIntegerField(db_index=True) 
    
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True) # Link to the table if it exists
    # ... (rest of the model is unchanged) # Link to the table if it exists
    table_name = models.CharField(max_length=100)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=7, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.kot_id}"