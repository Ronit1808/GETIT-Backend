from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.utils.crypto import get_random_string

# Create your models here.

class Product(models.Model):
    CATEGORY = (("Accessories" , "ACCESSORIES") ,
                ("Peripherals" , "PERIPHERALS"),
                ("PC Components" , "PC COMPONENTS"))
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(blank= True , null = True)
    image = models.ImageField(upload_to="img")
    description = models.TextField(blank=True , null=True)
    price = models.DecimalField(max_digits = 10 , decimal_places=2)
    category = models.CharField(max_length=15 , choices=CATEGORY , blank=True , null=True)
    
    
    def __str__(self):
        return self.name
    
    def save(self , *args , **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            unique_slug = self.slug
            counter = 1
            if Product.objects.filter(slug = unique_slug).exists():
                unique_slug = f'{self.slug} - {counter}'
                counter += 1
            self.slug = unique_slug
        
        super().save(*args , **kwargs)
    
class Cart(models.Model):
    cart_code = models.CharField(max_length=32, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE , default=1)
    paid = models.BooleanField (default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Generate unique cart code if it doesn't exist
        if not self.cart_code:
            self.cart_code = get_random_string(32)
        super().save(*args, **kwargs)
    
    
    def _str_(self):
        return self.cart_code
    
class CartItem (models.Model):
    cart = models.ForeignKey(Cart, related_name='items' , on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    
    def _str_(self):
        return f"{self.quantity} x {self.product.name} in cart {self.cart.id}"
    
    
class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=20, unique=True)
    razorpay_order_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    shipping_address = models.TextField(default='')
    payment_method = models.TextField(default='razorpay')
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    num_of_items = models.IntegerField()
    status = models.CharField(choices=ORDER_STATUS_CHOICES, max_length=20, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.order_id
    
    
    #keyid rzp_test_stxpngjf0fuOIL
    #keysecret fmUprCCteVBrL8drbbNU2QlC