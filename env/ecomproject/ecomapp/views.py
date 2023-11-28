from typing import Any
from django import http
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View, CreateView, FormView, DetailView, ListView
from django.urls import reverse_lazy, reverse
from .models import *
from .forms import CheckoutForm, CustomerRegistrationForm, CustomerLoginForm, ProductForm, PasswordForgotForm, PasswordResetForm
from django.contrib.auth import login, logout, authenticate
from django.db.models import Q
from django.core.paginator import Paginator
from django.views import View
from .utils import password_reset_token
from django.core.mail import send_mail
from django.conf import settings

class EcomMixin(object):
    def dispatch(self, request, *args, **kwargs):
        cart_id = request.session.get("cart_id")
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            if request.user.is_authenticated and hasattr(request.user, 'customer'):
                cart_obj.customer = request.user.customer
                cart_obj.save()
        return super().dispatch(request, *args, **kwargs)


class HomeView( TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context= super().get_context_data(**kwargs)

        all_products= Product.objects.all().order_by("-id")
        paginator= Paginator(all_products,8)
        page_number= self.request.GET.get('page')
        product_list= paginator.get_page(page_number)
        context['product_list']= product_list
        return context
    

class AllProductsView(TemplateView):
    template_name="allproducts.html"

    def get_context_data(self, **kwargs):
        context= super().get_context_data(**kwargs)
        context['allcategories']= Category.objects.all().order_by("-id")
        return context


class ProductDetailView(TemplateView):
    template_name= "productdetail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url_slug = self.kwargs['slug']
        product= Product.objects.get(slug= url_slug)
        product.view_count +=1
        product.save()
        context['product'] = product
        return context



class AddToCartView(TemplateView):
    template_name= "addtocart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        #get product id from requested url
        product_id = self.kwargs['pro_id']
        #get product
        product_obj = Product.objects.get(id=product_id)
        #check if cart exist
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            this_product_in_cart = cart_obj.cartproduct_set.filter(Product= product_obj)
            #check if cart product already exist in cart
            if this_product_in_cart.exists():
                cartproduct= this_product_in_cart.last()
                cartproduct.quantity += 1
                cartproduct.subtotal += product_obj.selling_price
                cartproduct.save()
                cart_obj.total += product_obj.selling_price
                cart_obj.save()
            else:
                cartproduct = CartProduct.objects.create(cart= cart_obj, Product= product_obj, rate=product_obj.selling_price, quantity= 1, subtotal= product_obj.selling_price)
                cart_obj.total += product_obj.selling_price
                cart_obj.save()

        else:
            cart_obj= Cart.objects.create(total=0)
            self.request.session['cart_id']= cart_obj.id
            cartproduct = CartProduct.objects.create(cart= cart_obj, Product= product_obj, rate=product_obj.selling_price, quantity= 1, subtotal= product_obj.selling_price)
            cart_obj.total += product_obj.selling_price
            cart_obj.save()

        # Get the current cart count
        cart_count = 0
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            cart_count = cart_obj.cartproduct_set.count()

        # Add cart count to the context
        context['cart_count'] = cart_count

        return context


class MyCartView(TemplateView):
    template_name= "mycart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cart_id= self.request.session.get('cart_id', None)
        if cart_id:
            cart= Cart.objects.get(id=cart_id)
        else:
            cart=None
        
        context['cart']=cart
        return context
    

class ManageCartView( View):
    def get(self, request, *args, **kwargs):
        cp_id = self.kwargs['cp_id']
        action= request.GET.get("action")
        cp_obj = CartProduct.objects.get(id=cp_id)
        cart_obj = cp_obj.cart

        if action=="inc":
            cp_obj.quantity +=1
            cp_obj.subtotal += cp_obj.rate
            cp_obj.save()
            cart_obj.total += cp_obj.rate
            cart_obj.save()

        elif action== "dcr":
            cp_obj.quantity -=1
            cp_obj.subtotal -= cp_obj.rate
            cp_obj.save()
            cart_obj.total -= cp_obj.rate
            cart_obj.save()

            if cp_obj.quantity == 0:
                cp_obj.delete()

        elif action =="rmv":
            cart_obj.total -= cp_obj.subtotal
            cart_obj.save()
            cp_obj.delete()

        else:
            pass
        return redirect("ecomapp:mycart")
    

class EmptyCartView(View):
    def get(self, request, *args, **kwargs):
        cart_id = request.session.get('cart_id', None)
        if cart_id:
            cart= Cart.objects.get(id= cart_id)
            cart.cartproduct_set.all().delete()
            cart.total= 0
            cart.save()
        return redirect("ecomapp:mycart")
    

class CheckoutView(EcomMixin, CreateView):
    template_name= 'checkout.html'
    form_class= CheckoutForm
    success_url= reverse_lazy('ecomapp:home')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not hasattr(request.user, 'customer'):
            # If the user is not authenticated or doesn't have a customer profile,
            # generate the registration page URL with a next parameter
            registration_url = reverse('ecomapp:customerregistration')
            redirect_url = f'{registration_url}?next={self.request.path}'
            return redirect(redirect_url)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cart_id= self.request.session.get('cart_id', None)
        if cart_id:
            cart= Cart.objects.get(id=cart_id)
        else:
            cart=None
        
        context['cart']=cart
        return context
    
    def form_valid(self, form):
        cart_id = self.request.session.get('cart_id')
        if cart_id:
            cart_obj= Cart.objects.get(id=cart_id)
            form.instance.cart= cart_obj
            form.instance.subtotal= cart_obj.total
            form.instance.discount= 0
            form.instance.total= cart_obj.total
            form.instance.order_status= "Order Received"
            del self.request.session['cart_id']
        else:
            return redirect("ecomapp:home")
        return super().form_valid(form)
        

class CustomerRegistrationView(CreateView):
    template_name= 'customerregistration.html'
    form_class = CustomerRegistrationForm
    success_url= reverse_lazy('ecomapp:home')

    def form_valid(self, form):
        username= form.cleaned_data.get('username')
        password= form.cleaned_data.get("password")
        email= form.cleaned_data.get('email')
        user= User.objects.create_user(username, email, password)

        form.instance.user= user
        login(self.request, user)
        return super().form_valid(form)
    
    def get_success_url(self):
        if "next" in self.request.GET:
            next_url = self.request.GET.get("next")
            return next_url
        else:
            return self.success_url
    

class CustomerLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("ecomapp:home")
    

class CustomerLoginView(FormView):
    template_name= 'customerlogin.html'
    form_class = CustomerLoginForm
    success_url= reverse_lazy('ecomapp:home')

    #form_valid method is a type of past method and is available in createview, formview and updateview
    def form_valid(self,form):
        uname= form.cleaned_data.get('username')
        pword= form.cleaned_data.get("password")

        usr= authenticate(username=uname, password= pword)
        if usr is not None and Customer.objects.filter(user=usr).exists():
            login(self.request, usr)
        else:
            return render(self.request, self.template_name, {"form":self.form_class, "error":"Invalid Credentials"})
        
        return super().form_valid(form)
    
    def get_success_url(self):
        if "next" in self.request.GET:
            next_url = self.request.GET.get("next")
            return next_url
        else:
            return self.success_url
        

class CustomerProfilView(TemplateView):
    template_name= "customerprofile.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            pass
        else:
            return redirect("/login/?next=/profile/")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context= super().get_context_data(**kwargs)
        customer= self.request.user.customer
        context['customer']=customer
        orders= Order.objects.filter(cart__customer=customer)
        context["orders"]=orders
        return context
    

class CustomerOrderDetailView(DetailView):
    template_name= "customerorderdetail.html"
    model= Order
    context_object_name= "ord_obj"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            order_id= self.kwargs['pk']
            order= Order.objects.get(id=order_id)
            if request.user.customer != order.cart.customer:
                return redirect("ecomapp:customerprofile")
        
        else:
            return redirect("/login/?next=/profile/")

        return super().dispatch(request, *args, **kwargs)
    

class AdminRequiredMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Admin.objects.filter(user=request.user).exists():
            pass
        else:
            return redirect("/admin-login/")
        return super().dispatch(request, *args, **kwargs)

class AdminLoginView(FormView):
    template_name= "adminpages/adminlogin.html"
    form_class= CustomerLoginForm
    success_url= reverse_lazy("ecomapp:adminhome")

    def form_valid(self, form):
        uname= form.cleaned_data.get("username")
        pword = form.cleaned_data["password"]
        usr= authenticate(username=uname, password=pword)
        if usr is not None and Admin.objects.filter(user=usr).exists():
            login(self.request, usr)
        else:
            return render(self.request, self.template_name, {"form":self.form_class, "error": "Invalid Credentials"})
        
        return super().form_valid(form)


class AdminHomeView(AdminRequiredMixin, TemplateView):
    template_name= "adminpages/adminhome.html"
    
    def get_context_data(self, **kwargs):
        context= super().get_context_data(**kwargs)
        context['pendingorders']= Order.objects.filter(order_status="Order Received").order_by("-id")

        return context


class AdminOrderDetailView(AdminRequiredMixin, DetailView):
    template_name= "adminpages/adminorderdetail.html"
    model= Order
    context_object_name= "ord_obj"

    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        context["allstatus"]= ORDER_STATUS
        return context


class AdminOrderListView(AdminRequiredMixin, ListView):
    template_name= "adminpages/adminorderlist.html"
    queryset= Order.objects.all().order_by("-id")
    context_object_name = "allorders"


class AdminOrderStatusChangeView(AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        order_id= self.kwargs["pk"]
        order_obj= Order.objects.get(id=order_id)
        
        new_status= request.POST.get('status')
        order_obj.order_status= new_status
        order_obj.save()
        return redirect(reverse_lazy("ecomapp:adminorderdetail", kwargs={"pk":order_id}))
    

class SearchView(TemplateView):
    template_name= "search.html"

    def get_context_data(self, **kwargs):
        context= super().get_context_data(**kwargs)
        kw= self.request.GET.get("keyword")
        results= Product.objects.filter(
            Q(title__icontains=kw)|
            Q(description__icontains=kw)|
            Q(return_policy__icontains=kw)
        )
        context["results"]=results
        return context

 
    
class AdminProductListView(AdminRequiredMixin, ListView):
    template_name= "adminpages/adminproductlist.html"
    queryset= Product.objects.all().order_by("-id")
    context_object_name= "allproducts"


class AdminProductCreateView(AdminRequiredMixin, CreateView):
    template_name= "adminpages/adminproductcreate.html"
    form_class= ProductForm
    success_url= reverse_lazy("ecomapp:adminproductlist")

    def form_valid(self, form):
        p= form.save()
        images= self.request.FILES.getlist("more_images")
        for i in images:
            ProductImage.objects.create(product=p, image=i)
        return super().form_valid(form)
    

class PasswordForgotView(FormView):
    template_name= "forgotpassword.html"
    form_class= PasswordForgotForm
    success_url="/forgot-password/?m=s"

    def form_valid(self, form):
        #get email from user
        email= form.cleaned_data.get('email')
        #get current host ip/domain
        url= self.request.META['HTTP_HOST']
        # get customer and then user
        customer = Customer.objects.get(user__email= email)
        user= customer.user

        # send mail to the user with email
        text_content= 'Please click the link below to reset your password. '
        html_content= url + "/password-reset/" + email + "/" + password_reset_token.make_token(user) + "/" 
        send_mail(
            'Password Reset Link | Django Ecommerce',
            text_content + html_content,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False
        )

        return super().form_valid(form)
    
class PasswordResetView(FormView):
    template_name= "passwordreset.html"
    form_class= PasswordResetForm
    success_url= "/login/"

    def dispatch(self, request, *args, **kwargs):
        email= self.kwargs.get("email")
        user= User.objects.get(email= email)
        token= self.kwargs.get("token")

        if user is not None and password_reset_token.check_token(user,token):
            pass
        else:
            return redirect(reverse("ecomapp:passwordforgot")+"?m=e")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        password= form.cleaned_data["new_password"]
        email= self.kwargs.get("email")
        user= User.objects.get(email= email)
        user.set_password(password)
        user.save()
        return super().form_valid(form)