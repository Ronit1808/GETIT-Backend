from rest_framework import serializers
from .models import Product , Cart , CartItem , Order
from django.contrib.auth import get_user_model

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id' , 'name' , 'slug' , 'image' , 'description' , 'category' , 'price']
        
        
class DetailedProductSerializer(serializers.ModelSerializer):
    similar_products = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ['id' , 'name' , 'slug' , 'image' , 'description' , 'price' , 'similar_products']
        
        
    def get_similar_products(self , product):
        products = Product.objects.filter(category = product.category).exclude(id = product.id)
        serializer = ProductSerializer(products , many = True)
        return serializer.data
    
        
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only = True)
    cart_item_total = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ["id", "quantity", "product" ,"cart_item_total"]
        
    def get_cart_item_total (self , cartitem):
        total = cartitem.product.price * cartitem.quantity
        return total
        
    
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(read_only = True , many = True)
    cart_total_price = serializers.SerializerMethodField()
    num_of_items = serializers.SerializerMethodField()
    
    
    class Meta:
        model = Cart
        fields = ["id", "cart_code", "created_at", "modified_at" ,"cart_total_price" , "items" , "num_of_items"]
        
    def get_cart_total_price (self , cart):
        items = cart.items.all()
        total = sum([item.product.price * item.quantity for item in items])
        return total

    def get_num_of_items (self , cart):
        items = cart.items.all()
        total = sum([item.quantity for item in items ])
        return total
    
    
class UserSerializer(serializers.ModelSerializer):
    cart_code = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ["id", "username", "email", "first_name", "last_name", "city", "address", "phone", "cart_code"]
    def get_cart_code(self, obj):
        try:
            # Fetch the most recent unpaid cart
            cart = Cart.objects.filter(user=obj, paid=False).order_by('-created_at').first()
            if cart:
                return cart.cart_code
            else:
                # If no unpaid cart exists, create one dynamically
                new_cart = Cart.objects.create(user=obj)
                return new_cart.cart_code
        except Exception as e:
            print(f"Error fetching or creating cart for user {obj.id}: {e}")
            return None

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'