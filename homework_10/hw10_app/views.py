from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Count

from .models import Author, Quote, Tag
from .forms import AuthorForm, QuoteForm, UserRegisterForm
from django.core.paginator import Paginator
import requests
from bs4 import BeautifulSoup

from django.views.generic import TemplateView, ListView

# Create your views here.
def home(request):
    return render(request, 'hw10_app/home.html')


class HomeView(TemplateView):
    template_name = 'hw10_app/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['authors'] = Author.objects.all()
        context['quotes'] = Quote.objects.all()
        return context


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'hw10_app/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'hw10_app/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def add_author(request):
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = AuthorForm()
    return render(request, 'hw10_app/add_author.html', {'form': form})


@login_required
def add_quote(request):
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = QuoteForm()
    return render(request, 'hw10_app/add_quote.html', {'form': form})


@login_required
def scrape(request):
    base_url = 'http://quotes.toscrape.com'
    page_number = 1

    while True:
        url = f'{base_url}/page/{page_number}/'
        response = requests.get(url)
        
        if response.status_code != 200:
            break
        
        soup = BeautifulSoup(response.text, 'html.parser')
        quotes_to_scrape = soup.find_all('div', class_='quote')
        for quote in quotes_to_scrape:
            quote_text = quote.find('span', class_='text').get_text()
            author_name = quote.find('small', class_='author').get_text()
            
            tags_meta = quote.find('meta', itemprop='keywords')
            if tags_meta:
                tags = tags_meta['content'].split(',')
            else:
                tags = []

            author, created = Author.objects.get_or_create(name=author_name)
            quote_obj, created = Quote.objects.get_or_create(text=quote_text, author=author)

            for tag_name in tags:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                quote_obj.tags.add(tag)

        next_page = soup.find('li', class_='next')
        if next_page:
            page_number += 1
        else:
            break
    return redirect('home')


def author_list(request):
    authors = Author.objects.all()
    paginator = Paginator(authors, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'hw10_app/author_list.html', {'page_obj': page_obj})


def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk)
    quotes = Quote.objects.filter(author=author)
    return render(request, 'hw10_app/author_detail.html', {'author': author, 'quotes': quotes})


def quote_list(request):
    quotes = Quote.objects.all()
    paginator = Paginator(quotes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    top_tags = Tag.objects.annotate(num_quotes=Count('quote')).order_by('-num_quotes')[:10]
    return render(request, 'hw10_app/quote_list.html', {'page_obj': page_obj, 'top_tags': top_tags})


def quotes_by_tag(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    quotes = Quote.objects.filter(tags=tag)
    paginator = Paginator(quotes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'hw10_app/quotes_by_tag.html', {'page_obj': page_obj, 'tag': tag})