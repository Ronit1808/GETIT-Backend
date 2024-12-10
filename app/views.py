
from .models import Product ,Cart , CartItem,Order
from .serializers import ProductSerializer , DetailedProductSerializer , CartItemSerializer , CartSerializer ,UserSerializer , OrderSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings

from razorpay.errors import SignatureVerificationError

import razorpay
import uuid
import logging

CustomUser = get_user_model()
# Create your views here.

@api_view(["GET"])
def products(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products , many= True)
    return Response(serializer.data)


@api_view(["GET"])
def product_detail(request , slug):
    product = Product.objects.get(slug = slug)
    serializer = DetailedProductSerializer(product)
    return Response(serializer.data)


@api_view(["POST"])
def add_item(request):
    try:
        cart_code = request.data.get("cart_code")
        product_id = request.data.get("product_id")
        
        cart = Cart.objects.get (cart_code = cart_code)
        product = Product.objects.get(id=product_id)
        
        cartitem, created = CartItem.objects.get_or_create(cart = cart , product = product)
        cartitem.quantity = 1
        cartitem.save()
        
        serializer = CartItemSerializer (cartitem)
        return Response({"data": serializer.data, "message" : "Item Added Sucessfully"} , status=201)
    
    except Exception as e:
        return Response({ "error": str(e)}, status=400)
    
    

@api_view(["GET"])
def product_is_added(request):
    cart_code = request.query_params.get("cart_code")
    product_id = request.query_params.get("product_id")
    
    cart = Cart.objects.get(cart_code = cart_code)
    product = Product.objects.get(id = product_id)
    
    product_exist = CartItem.objects.filter(cart = cart , product = product).exists()
    
    return Response({'product_is_added' : product_exist})
 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart(request):
    try:
        # Use the logged-in user to fetch the cart
        cart_code = request.query_params.get("cart_code")
        cart = Cart.objects.get(user=request.user ,paid=False , cart_code = cart_code)
        # Return cart data, including the items, total price, etc.
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found for this user'}, status=404)
    
    
@api_view(["PATCH"])
def update_quantity(request , item_id):
    try:
        cartitem = CartItem.objects.get(id = item_id)
        new_quantity = request.data.get("quantity")
        if new_quantity is not None and int(new_quantity) > 0 :
            cartitem.quantity = new_quantity
            cartitem.save()
            cart = cartitem.cart
            serializer = CartSerializer(cart)
            return Response({"data" : serializer.data , "message" : "Item updated successfully"})
        else:
            return Response({"error" : "invalid Quantity"} , status=400)
            
    except CartItem.DoesNotExist :
        return Response({"error" : "Item not found"} , status=401)
        
        
@api_view(["DELETE"])
def delete_item(request , item_id) :
    try:
        cartitem = CartItem.objects.get(id = item_id)
        cart = cartitem.cart
        cartitem.delete()
        
        serializer = CartSerializer(cart)
        return Response({"data" : serializer.data , "message" : "Item deleted sucessfully"})
        
    except CartItem.DoesNotExist:
        return Response({"error" : "Item not Found"} , status=404)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)

    
    

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if CustomUser.objects.filter(username=username).exists():
        return Response({"message": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

    if CustomUser.objects.filter(email=email).exists():
        return Response({"message": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)

    user = CustomUser.objects.create(
        username=username,
        email=email,
        password=make_password(password)  
    )
    cart = Cart.objects.create(user=user)
    user.save()

    return Response({"message": "User created successfully", 'cart_code': cart.cart_code} , status=status.HTTP_201_CREATED)

    
    
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    user = request.user
    try:
        cart_items = CartItem.objects.filter(cart__user=user)
        cart_items.delete()
        return Response({"message": "Cart cleared successfully!"}, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=400)
    
    
 


razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def generate_order_id():
    return str(uuid.uuid4()).replace('-', '').upper()[:10]

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_order(request):
    try:
        user = request.user
        cart_code = request.data.get('cart_code')
        shipping = request.data.get('shipping')
        payment_method = request.data.get('payment_method')
        print("Request data:", request.data)

        if not cart_code or not shipping or not payment_method:
            return Response({"error": "Missing required fields"}, status=400)

        try:
             cart = Cart.objects.filter(user=user, paid=False, cart_code=cart_code).first()
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found for the user."}, status=404)
        
        if Order.objects.filter(cart=cart).exists():
            return Response({"error": "Order already exists for this cart."}, status=400)

        
        cart_items = cart.items.all()
        total_price = sum(item.product.price * item.quantity for item in cart_items)
        num_of_items = sum(item.quantity for item in cart_items)

        if total_price <= 0:
            return Response({"error": "Cart total price must be greater than zero."}, status=400)
        

        with transaction.atomic():
          
            order = Order.objects.create(
                user=user,
                cart=cart,
                total_price=total_price,
                num_of_items=num_of_items,
                order_id=generate_order_id(),
                status='Pending',
                shipping_address = shipping,
                payment_method = payment_method
                
            )
            

            
            cart.paid = True
            old_cart_code = cart_code
            cart.save()


            new_cart = Cart.objects.create(user=user)


            if(payment_method == 'razorpay'):
          
                razorpay_order = razorpay_client.order.create(dict(
                    amount=int(total_price * 100),  # Amount in paise
                    currency='INR',
                    receipt=str(order.id),
                    notes={'cart_code': old_cart_code}
                ))
                razorpay_order_id = razorpay_order['id']
                order.razorpay_order_id = razorpay_order_id
                order.save()
                
                
                return Response({
                'order_id': order.order_id,
                'razorpay_order_id': razorpay_order_id,
                'amount': total_price,
                'currency': 'INR',
                'status': 'Order Created',
                'receipt': str(order.id),
                'cart_code' : new_cart.cart_code,
            })
            
            elif payment_method == 'paypal':
                pass

    except Exception as e:
        print(f"Error: {e}")
        return Response({"error": "An error occurred while processing the order.", "details": str(e)}, status=500)


logger = logging.getLogger(__name__)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
   
    try:
        logger.info("Payment verification data: %s", request.data)

        
        payment_id = request.data.get('razorpay_payment_id')
        razorpay_order_id = request.data.get('razorpay_order_id')
        signature = request.data.get('razorpay_signature')

        
        if not (payment_id and razorpay_order_id and signature):
            return Response({'error': 'Missing required payment details'}, status=status.HTTP_400_BAD_REQUEST)

        
        params = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        razorpay_client.utility.verify_payment_signature(params)

       
        try:
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)  # Match Razorpay's order ID
            order.status = 'Completed'
            order.save()
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'status': 'Payment verified successfully!'}, status=status.HTTP_200_OK)

    except SignatureVerificationError:
        return Response({'error': 'Invalid payment signature'}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        
        print(str(e))
        return Response({'error': 'Error during payment verification', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request , order_id):
        try:
            order = Order.objects.get(order_id=order_id, user=request.user)
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=200)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
        
 
 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_orders(request):
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)