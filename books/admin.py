from django.contrib import admin
from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'authors', 'average_rating', 'publication_date', 'language_code', 'num_pages')
    list_filter = ('language_code', 'average_rating')
    search_fields = ('title', 'authors', 'isbn', 'isbn13', 'publisher')
    list_per_page = 50
