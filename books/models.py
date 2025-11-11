from django.db import models


class Book(models.Model):
    """Model representing a book in the database."""

    bookID = models.IntegerField(db_index=True)
    title = models.CharField(max_length=500, db_index=True)
    authors = models.CharField(max_length=500, db_index=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, db_index=True)
    isbn = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    isbn13 = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    language_code = models.CharField(max_length=10, db_index=True)
    num_pages = models.IntegerField(null=True, blank=True, db_index=True)
    ratings_count = models.IntegerField(default=0, db_index=True)
    text_reviews_count = models.IntegerField(default=0, db_index=True)
    publication_date = models.DateField(null=True, blank=True, db_index=True)
    publisher = models.CharField(max_length=500, null=True, blank=True, db_index=True)

    class Meta:
        ordering = ['-average_rating', 'title']
        indexes = [
            models.Index(fields=['title', 'authors']),
            models.Index(fields=['average_rating', 'ratings_count']),
        ]

    def __str__(self):
        return f"{self.title} by {self.authors}"
