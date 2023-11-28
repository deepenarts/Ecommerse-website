from django.db import models
from django.contrib.auth.models import User


class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name= models.CharField(max_length=50)
    image= models.ImageField(upload_to="admins", default="images/admin.png")
    mobile=models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.user.username

class Customer(models.Model):
    user= models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    full_name= models.CharField(max_length=200)
    address= models.CharField(max_length=200, null=True, blank=True)
    joined_on = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.full_name
    

class Category(models.Model):
    title=  models.CharField(max_length=200)
    slug= models.SlugField(unique=True)

    def __str__(self) -> str:
        return self.title
    

class Product(models.Model):
    title= models.CharField(max_length=200)
    slug= models.SlugField(unique=True)
    Category= models.ForeignKey(Category, on_delete=models.CASCADE)
    image= models.ImageField(upload_to='productts')
    marked_price = models.PositiveIntegerField()
    selling_price = models.PositiveIntegerField()
    description = models.TextField()
    warrenty= models.CharField(max_length=300, null=True, blank=True)
    return_policy= models.CharField(max_length=300, null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return self.title
    

class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    total = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return 'Cart: '+ str(self.id)
    

class CartProduct(models.Model):
    cart= models.ForeignKey(Cart, on_delete=models.CASCADE)
    Product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rate= models.PositiveBigIntegerField()
    quantity= models.PositiveIntegerField()
    subtotal = models.PositiveIntegerField()

    def __str__(self) -> str:
        return 'Cart: ' + str(self.cart.id) + ' CartProduct: '+ str(self.id)
    

ORDER_STATUS = (
    ('Order Received', 'Order Received'),
    ('Order Processing', 'Order Processing'),
    ('On the way', 'On the way'),
    ('Order Completed', 'Order Completed'),
    ('Order Cancelled', 'Order Cancelled'),
)

class Order(models.Model):
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE)
    ordered_by= models.CharField(max_length=200)
    shipping_address= models.CharField(max_length=200)
    mobile= models.CharField(max_length=10)
    email= models.EmailField(null=True, blank=True)
    subtotal= models.PositiveIntegerField()
    discount= models.PositiveIntegerField()
    total= models.PositiveIntegerField()
    order_status= models.CharField(max_length=50, choices=ORDER_STATUS)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return 'Order: '+ str(self.id)


class ProductImage(models.Model):
    product= models.ForeignKey(Product, on_delete=models.CASCADE)
    image= models.ImageField(upload_to='products/images/')

    def __str__(self):
        return self.product.title
    