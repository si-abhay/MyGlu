from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ProfileCreationForm, AccountUpdateForm, GrievanceForm, RegistrationForm, BlogForm
from .models import Profile, Grievance, Post, Tag, Category
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from paypal.standard.forms import PayPalPaymentsForm
from urllib.parse import urlencode
from .models import Request
from datetime import date, timedelta

import uuid
from django.urls import reverse
from django.shortcuts import redirect

# Create your views here.


def register(request):
    if request.method == 'POST':
        form = ProfileCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! Please log in.')
            return redirect('login')
    else:
        form = ProfileCreationForm()
    return render(request, 'user/register.html', {'form': form})

from django.shortcuts import get_object_or_404

def reg_final(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            profile = get_object_or_404(Profile, username=request.user.username)
            profile.name = form.cleaned_data.get('name')
            profile.registered_address = form.cleaned_data.get('registered_address')
            profile.area_of_operation = form.cleaned_data.get('area_of_operation')
            profile.license_no = form.cleaned_data.get('license_no')
            profile.phone = form.cleaned_data.get('phone')
            profile.service_tax_no = form.cleaned_data.get('service_tax_no')
            profile.state = form.cleaned_data.get('state')
            profile.district = form.cleaned_data.get('district')
            profile.hospital = form.cleaned_data.get('hospital')
            profile.designation = form.cleaned_data.get('designation')
            profile.is_registered = True
            profile.save()

            messages.success(request, f'Details will be reviewed by admin.')
            return redirect('profile')
    else:
        form = RegistrationForm()
    return render(request, 'user/reg_final.html', {'form': form})


def grievances_view(request):
    societies = Profile.objects.all()
    if request.method == 'POST':
        form = GrievanceForm(request.POST)
        if form.is_valid():
            grievance = form.save(commit=False)
            messages.success(request, f'Your complaint/feedback has been recorded.')
            grievance.save()  # Save the grievance object to the database
            return redirect('home')
        else:
            print(form.errors)  # Print the form errors to the console for debugging purposes
    else:
        form = GrievanceForm()
    return render(request, 'user/grievances.html', {'form': form, 'Profile': Profile})

from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

def blog(request):
    query = request.GET.get('q')
    blog_posts = Post.objects.all().order_by('-date')
    categories = Category.objects.all()

    if query:
        # Filter the blog_posts based on the search query
        blog_posts = blog_posts.filter(Q(title__icontains=query) | Q(content__icontains=query) | Q(author__icontains=query))

     # pages with 4 posts per page
    paginator = Paginator(blog_posts, 4)

    page_number = request.GET.get('page')  # current page number
    blog_posts = paginator.get_page(page_number)  # Get the blog posts for the specified page number
    
    tags = Tag.objects.all() 
    return render(request, 'user/blog.html', {'blog_posts': blog_posts, 'categories': categories, 'tags': tags})

def blog_category(request, category_id):
    category = Category.objects.get(id=category_id)
    blog_posts = Post.objects.filter(category=category).order_by('-date')
    categories = Category.objects.all() 
    tags = Tag.objects.all() 
    return render(request, 'user/blog.html', {'blog_posts': blog_posts, 'categories': categories, 'tags': tags})

def blog_tag(request, tag_id):
    tag = Tag.objects.get(id=tag_id) 
    blog_posts = Post.objects.filter(tags=tag).order_by('-date')
    categories = Category.objects.all()
    tags = Tag.objects.all() 
    return render(request, 'user/blog.html', {'blog_posts': blog_posts, 'categories': categories, 'tags': tags})


def blogsingle(request):
    return render(request, 'user/blogsingle.html')



@login_required 
def profile(request):
    return render(request, 'user/profile.html')
    

@login_required
def payment_page(request):
    host = request.get_host()
    id = request.user.id

    paypal_dict = {
                'business': settings.PAYPAL_RECEIVER_EMAIL,
                'amount': '30.00',
                'item_name': 'Annual Fee Payment',
                'invoice': str(uuid.uuid4()),
                'currency_code': 'USD',
                'notify_url': f'http:/{host}{reverse("paypal-ipn")}',
                'return_url': f'http://{host}{reverse("payment_done")}?{urlencode({"id": id})}',
                'cancel_return': f'http:/{host}{reverse("payment_cancelled")}',
            }
    form = PayPalPaymentsForm(initial=paypal_dict)
    context = {'form': form}  
    return render(request, 'user/payment_page.html', context)

from django.views.decorators.csrf import csrf_exempt

#######===== PROCESS PAYMENT=====########
@csrf_exempt
def payment_done(request):
    if request.method == 'GET':
        context = request.GET
        profile = Profile.objects.get(id=context['id'])
        profile.is_paid = True
        profile.save()
        messages.success(request, 'Payment was successful.')
        return redirect('profile')
    elif request.method == 'POST':
        context = request.POST
        profile = Profile.objects.get(id=context['id'])
        profile.is_paid = True
        profile.save()
        messages.success(request, 'Payment was successful.')
        return redirect('profile')
    messages.warning(request, 'Payment was successful.')
    return redirect('profile')



@csrf_exempt
def payment_cancelled(request):
    messages.warning(request, 'Payment was cancelled.')
    return redirect('profile')


@login_required
def update_profile(request):
    if request.method == 'POST':
        form = AccountUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Your account has been updated.')
            return render(request,'user/profile.html')
    else:
        form = AccountUpdateForm(instance=request.user)
    return render(request, 'user/update_profile.html', {'form': form})


@login_required
def view_profile(request):
    return render(request, 'user/view_profile.html', {'user': request.user})

@login_required
def submit_request(request):
    if request.method == 'POST':
        request_text = request.POST.get('request_text')
        
        profile = Profile.objects.get(username=request.user)
        # Create a new Request object and save it to the database
        new_request = Request(username=profile, request_text=request_text)
        
        # Set the request number and status accordingly
        new_request.request_number = new_request.id  # Assuming request_number is the ID of the request object
        new_request.status = 'Pending'
        new_request.save()
        
        return redirect('profile') 
    
    return render(request, 'user/submit_request.html')


@login_required
def create_blog(request):
    if request.method == 'POST':
        # Handle form submission for creating a new blog post
        form = BlogForm(request.POST)
        if form.is_valid():
            # Save the new blog post
            blog_post = form.save(commit=False)
            blog_post.author = request.user.username
            blog_post.username_id = request.user.id
            blog_post.save()
            form.save_m2m() 
            messages.success(request, f'Your blog post has been created.')

            return redirect('profile')
    else:
        # Render the form for creating a new blog post
        form = BlogForm()
    
    return render(request, 'user/create_blog.html', {'form': form})
