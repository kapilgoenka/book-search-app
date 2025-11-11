# Product Requirements Document (PRD)
## Book Search Web Application

---

## 1. Overview

### 1.1 Product Summary
A Django-based web application that enables users to search and browse a collection of books using various search criteria. The application provides an intuitive interface for filtering books by multiple attributes including title, author, ratings, publication details, and more.

### 1.2 Problem Statement
Users need an efficient way to search and discover books from a large dataset based on multiple criteria such as title, author, ratings, page count, and publication details.

### 1.3 Target Users
- Book enthusiasts looking to discover books
- Readers searching for books based on specific criteria
- Users wanting to filter books by ratings, page count, or publication date
- Anyone needing to search through a comprehensive book database

---

## 2. Technical Stack

### 2.1 Backend
- **Framework**: Django (Python)
- **Package Management**: UV
- **Database**: SQLite

### 2.2 Frontend
- HTML/CSS
- JavaScript (for dynamic interactions)
- Django Templates

### 2.3 Data Source
- **Source URL**: https://github.com/MainakRepositor/Datasets/blob/master/books.csv
- **Format**: CSV file containing book metadata

---

## 3. Database Requirements

### 3.1 Database Schema

**Table: Books**

| Field Name | Type | Description | Constraints |
|------------|------|-------------|-------------|
| id | Integer | Primary key | Auto-increment |
| bookID | Integer | Book identifier | From dataset |
| title | String | Book title | Max 500 chars |
| authors | String | Book author(s) | Max 500 chars |
| average_rating | Decimal | Average rating score | Decimal(3,2) |
| isbn | String | ISBN number | Max 20 chars, nullable |
| isbn13 | String | ISBN-13 number | Max 20 chars, nullable |
| language_code | String | Language code | Max 10 chars |
| num_pages | Integer | Number of pages | Nullable |
| ratings_count | Integer | Total ratings count | Default 0 |
| text_reviews_count | Integer | Total text reviews | Default 0 |
| publication_date | Date | Publication date | Nullable |
| publisher | String | Publisher name | Max 500 chars, nullable |

### 3.2 Data Import
- Import data from the CSV file during initial setup
- Create a Django management command for data import
- Handle data validation and error cases during import

---

## 4. Functional Requirements

### 4.1 Search Functionality

The application must support the following search filters:

| Search Field | Search Type | Implementation |
|--------------|-------------|----------------|
| Title | Substring search | Case-insensitive contains |
| Authors | Substring search | Case-insensitive contains |
| Average Rating | Range filter | Greater than or equal to (≥) AND/OR Less than or equal to (≤) |
| ISBN | Exact match | Case-insensitive exact match |
| ISBN13 | Exact match | Case-insensitive exact match |
| Language Code | Single select | Dropdown populated from available languages |
| Number of Pages | Range filter | Greater than or equal to (≥) AND/OR Less than or equal to (≤) |
| Ratings Count | Range filter | Greater than or equal to (≥) AND/OR Less than or equal to (≤) |
| Text Reviews Count | Range filter | Greater than or equal to (≥) AND/OR Less than or equal to (≤) |
| Publication Date | Range filter | Greater than or equal to (≥) AND/OR Less than or equal to (≤) |
| Publisher | Substring search | Case-insensitive contains |

### 4.2 Search Behavior
- All search filters are optional
- Multiple filters can be applied simultaneously (AND logic)
- Empty search (no filters applied) should return all books or show a message
- Search results should update when the search form is submitted
- Display meaningful messages when no results are found

### 4.3 Results Display
- Show search results in a table or card layout
- Display the following fields for each book:
  - Thumbnail image (if available)
  - Title
  - Author(s)
  - Average rating
  - Publication date
  - Publisher
  - Number of pages
  - ISBN/ISBN13
  - Language
- Implement pagination for large result sets (e.g., 25-50 results per page)

### 4.4 Book Thumbnails
- Integrate with a web-based resource or API to fetch book cover images
- Recommended APIs:
  - Google Books API
  - Open Library Covers API
  - ISBN Database API
- Use ISBN or ISBN13 as the lookup key
- Provide a placeholder image for books without available covers
- Handle API failures gracefully with fallback images

---

## 5. User Interface Requirements

### 5.1 Layout Structure

```
+--------------------------------------------------+
|                    HEADER                         |
|  (Application title, navigation, etc.)           |
+--------------------------------------------------+
|                                                   |
|  +------------------+  +----------------------+  |
|  |                  |  |                      |  |
|  |  SEARCH PANEL    |  |   RESULTS PANEL      |  |
|  |  (Left Pane)     |  |   (Right Pane)       |  |
|  |                  |  |                      |  |
|  |  - Title         |  |   - Book 1           |  |
|  |  - Authors       |  |   - Book 2           |  |
|  |  - Rating        |  |   - Book 3           |  |
|  |  - ISBN          |  |   - ...              |  |
|  |  - Language      |  |   - Pagination       |  |
|  |  - Pages         |  |                      |  |
|  |  - ...           |  |                      |  |
|  |  [Search Button] |  |                      |  |
|  |                  |  |                      |  |
|  +------------------+  +----------------------+  |
|                                                   |
+--------------------------------------------------+
```

### 5.2 Header Section
- Application title: "Book Search"
- Optional: Navigation links, user info, or additional features
- Clean, professional design
- Responsive across devices

### 5.3 Left Pane - Search Panel
- Form with all search filters organized logically
- Group related fields together:
  - Basic info: Title, Authors, Publisher
  - Identifiers: ISBN, ISBN13
  - Ratings & Reviews: Average Rating, Ratings Count, Text Reviews Count
  - Publication: Language, Publication Date
  - Physical: Number of Pages
- Clear labels for each field
- For range filters, provide two input fields:
  - "Minimum" (≥)
  - "Maximum" (≤)
- Language dropdown populated dynamically from database
- Clear/Reset button to clear all filters
- Search/Submit button
- Responsive design that collapses on mobile devices

### 5.4 Right Pane - Results Panel
- Display search results in a grid or list layout
- Each book card/row should include:
  - Thumbnail (left-aligned)
  - Title (bold, prominent)
  - Author(s)
  - Average rating (with star visualization if possible)
  - Publication date and publisher
  - Page count
  - Language
  - ISBN/ISBN13 (smaller text)
- Show result count (e.g., "Showing 25 of 150 results")
- Pagination controls at bottom
- Loading indicator during search
- Empty state message when no results found
- Responsive grid that adjusts column count based on screen size

### 5.5 Responsive Design
- Desktop: Two-pane layout (30% left, 70% right)
- Tablet: Two-pane layout with adjusted proportions
- Mobile: Stacked layout (search on top, collapsible; results below)

---

## 6. Non-Functional Requirements

### 6.1 Performance
- Page load time: < 2 seconds
- Search response time: < 1 second for queries on the dataset
- Efficient database queries using Django ORM with proper indexing

### 6.2 Usability
- Intuitive interface requiring no training
- Clear error messages and validation feedback
- Accessible design following WCAG 2.1 guidelines (AA level)

### 6.3 Scalability
- Architecture should support future database migration (SQLite → PostgreSQL/MySQL)
- Modular code structure for easy feature additions

### 6.4 Security
- Input validation and sanitization to prevent SQL injection
- CSRF protection (Django default)
- No sensitive data exposure

### 6.5 Browser Compatibility
- Support for modern browsers:
  - Chrome (latest 2 versions)
  - Firefox (latest 2 versions)
  - Safari (latest 2 versions)
  - Edge (latest 2 versions)

---

## 7. Project Deliverables

### 7.1 MVP (Minimum Viable Product)
1. Django application with UV package management setup
2. SQLite database with Books table
3. Data import script/command for CSV data
4. Search functionality with all specified filters
5. Basic UI with two-pane layout
6. Results display with pagination
7. Book thumbnail integration (basic implementation)

### 7.2 Future Enhancements (Out of Scope for MVP)
- User authentication and saved searches
- Book details page with more information
- Export search results (CSV, PDF)
- Advanced sorting options
- Book recommendations based on search history
- User reviews and ratings
- Wishlist/favorites functionality
- Social sharing features
- Admin panel for data management

---

## 8. Development Phases

### Phase 1: Setup & Infrastructure
- Initialize Django project with UV
- Set up SQLite database
- Create Books model
- Implement CSV data import command
- Basic project structure

### Phase 2: Backend Development
- Implement search view and logic
- Create querysets with filter logic
- Add pagination
- API integration for book thumbnails

### Phase 3: Frontend Development
- Create base templates
- Implement header and layout
- Build search form (left pane)
- Build results display (right pane)
- Add responsive CSS

### Phase 4: Integration & Polish
- Connect frontend with backend
- Add loading states and error handling
- Implement book thumbnail display
- Cross-browser testing

### Phase 5: Testing & Deployment
- Unit tests for models and views
- Integration tests for search functionality
- User acceptance testing
- Documentation
- Deployment setup

---

## 9. Success Metrics

- Search functionality works correctly for all filter types
- Search results are accurate and relevant
- Page load and search response times meet requirements
- UI is intuitive and responsive across devices
- At least 80% of books have thumbnail images displayed
- No critical bugs in production

---

## 10. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| CSV data quality issues | Medium | Implement robust error handling in import script |
| Book thumbnail API rate limits | Low | Implement caching, use multiple fallback APIs |
| Large dataset performance | Medium | Add database indexes, implement efficient pagination |
| CSV file structure changes | Low | Version control data schema, validate during import |

---

## 11. Assumptions

- The CSV file structure remains consistent
- Internet connectivity is available for thumbnail API calls
- Users have modern web browsers
- The dataset size is manageable for SQLite (< 100K records)
- Book thumbnail APIs are freely available

---

## 12. Dependencies

- UV package manager installed
- Python 3.10+ installed
- Internet connection for API calls
- Access to the CSV data file

---

## 13. Appendix

### 13.1 Useful Resources
- Django Documentation: https://docs.djangoproject.com/
- UV Documentation: https://github.com/astral-sh/uv
- Google Books API: https://developers.google.com/books
- Open Library Covers API: https://openlibrary.org/dev/docs/api/covers

### 13.2 Contact Information
- Product Owner: [To be filled]
- Technical Lead: [To be filled]
- Project Start Date: [To be filled]

---

**Document Version**: 1.0
**Last Updated**: 2025-11-11
**Status**: Draft
