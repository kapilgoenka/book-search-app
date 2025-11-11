from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Book


def book_search(request):
    """View for searching books with multiple filters."""

    # Start with all books
    books = Book.objects.all()

    # Get unique language codes for dropdown
    language_codes = Book.objects.values_list('language_code', flat=True).distinct().order_by('language_code')

    # Initialize filter flags
    filters_applied = False

    # Apply filters based on GET parameters
    if request.GET:
        # Title (substring search)
        title = request.GET.get('title', '').strip()
        if title:
            books = books.filter(title__icontains=title)
            filters_applied = True

        # Authors (substring search)
        authors = request.GET.get('authors', '').strip()
        if authors:
            books = books.filter(authors__icontains=authors)
            filters_applied = True

        # Average rating (range)
        avg_rating_min = request.GET.get('avg_rating_min', '').strip()
        if avg_rating_min:
            try:
                books = books.filter(average_rating__gte=float(avg_rating_min))
                filters_applied = True
            except ValueError:
                pass

        avg_rating_max = request.GET.get('avg_rating_max', '').strip()
        if avg_rating_max:
            try:
                books = books.filter(average_rating__lte=float(avg_rating_max))
                filters_applied = True
            except ValueError:
                pass

        # ISBN (exact match)
        isbn = request.GET.get('isbn', '').strip()
        if isbn:
            books = books.filter(isbn__iexact=isbn)
            filters_applied = True

        # ISBN13 (exact match)
        isbn13 = request.GET.get('isbn13', '').strip()
        if isbn13:
            books = books.filter(isbn13__iexact=isbn13)
            filters_applied = True

        # Language code (dropdown)
        language_code = request.GET.get('language_code', '').strip()
        if language_code:
            books = books.filter(language_code=language_code)
            filters_applied = True

        # Number of pages (range)
        num_pages_min = request.GET.get('num_pages_min', '').strip()
        if num_pages_min:
            try:
                books = books.filter(num_pages__gte=int(num_pages_min))
                filters_applied = True
            except ValueError:
                pass

        num_pages_max = request.GET.get('num_pages_max', '').strip()
        if num_pages_max:
            try:
                books = books.filter(num_pages__lte=int(num_pages_max))
                filters_applied = True
            except ValueError:
                pass

        # Ratings count (range)
        ratings_count_min = request.GET.get('ratings_count_min', '').strip()
        if ratings_count_min:
            try:
                books = books.filter(ratings_count__gte=int(ratings_count_min))
                filters_applied = True
            except ValueError:
                pass

        ratings_count_max = request.GET.get('ratings_count_max', '').strip()
        if ratings_count_max:
            try:
                books = books.filter(ratings_count__lte=int(ratings_count_max))
                filters_applied = True
            except ValueError:
                pass

        # Text reviews count (range)
        text_reviews_min = request.GET.get('text_reviews_min', '').strip()
        if text_reviews_min:
            try:
                books = books.filter(text_reviews_count__gte=int(text_reviews_min))
                filters_applied = True
            except ValueError:
                pass

        text_reviews_max = request.GET.get('text_reviews_max', '').strip()
        if text_reviews_max:
            try:
                books = books.filter(text_reviews_count__lte=int(text_reviews_max))
                filters_applied = True
            except ValueError:
                pass

        # Publication date (range)
        pub_date_min = request.GET.get('pub_date_min', '').strip()
        if pub_date_min:
            try:
                books = books.filter(publication_date__gte=pub_date_min)
                filters_applied = True
            except Exception:
                pass

        pub_date_max = request.GET.get('pub_date_max', '').strip()
        if pub_date_max:
            try:
                books = books.filter(publication_date__lte=pub_date_max)
                filters_applied = True
            except Exception:
                pass

        # Publisher (substring search)
        publisher = request.GET.get('publisher', '').strip()
        if publisher:
            books = books.filter(publisher__icontains=publisher)
            filters_applied = True

    # Pagination
    paginator = Paginator(books, 25)  # 25 books per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'language_codes': language_codes,
        'filters_applied': filters_applied,
        'total_results': paginator.count,
    }

    return render(request, 'books/search.html', context)
