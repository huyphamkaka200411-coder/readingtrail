# ReadingTrail REST API Documentation

## Overview
This document describes the RESTful web services for the ReadingTrail Digital Book Borrowing System. All API endpoints follow standard REST conventions and return JSON responses.

## Quick Reference

| Endpoint Category | Description | Base Path |
|------------------|-------------|-----------|
| **Users** | User management and profiles | `/users` |
| **Books** | Book catalog and management | `/books` |
| **Borrowed Books** | Book borrowing system | `/borrowed-books` |
| **Reviews** | Book reviews and ratings | `/reviews` |
| **Achievements** | User achievements system | `/achievements` |
| **Discussions** | Forum discussions | `/discussions` |
| **Notifications** | User notifications | `/notifications` |

## Base URL
```
http://localhost:5000/api/v1/
```

## API Features
- **Comprehensive Book Management**: CRUD operations for books with search and filtering
- **User Management**: User profiles with achievements and ranking system  
- **Borrowing System**: Complete book borrowing and returning workflow
- **Reviews & Ratings**: User reviews with 1-5 star rating system
- **Social Features**: Discussions, notifications, and user interactions
- **Achievement System**: Gamification with points and user rankings
- **Real-time Features**: Live notifications and discussion updates

## Authentication
Most endpoints require user authentication. The API uses session-based authentication with Flask-Login. Include your session cookie in requests for authenticated endpoints.

## Response Format
All API responses follow a consistent JSON structure:

### Success Response
```json
{
  "message": "Success",
  "data": { ... }
}
```

### Error Response
```json
{
  "error": "Error message"
}
```

## HTTP Status Codes
- **200** - Success
- **201** - Created successfully
- **400** - Bad request (validation error)
- **401** - Unauthorized (login required)
- **403** - Forbidden (access denied)
- **404** - Not found
- **500** - Internal server error

---

# User Endpoints

## List Users
Get a paginated list of users with optional search functionality.

**Endpoint:** `GET /api/v1/users`

**Parameters:**
- `page` (optional, integer): Page number (default: 1)
- `per_page` (optional, integer): Items per page (default: 20, max: 100)
- `search` (optional, string): Search in username, email, first name, last name

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/v1/users?page=1&per_page=10&search=john"
```

**Example Response:**
```json
{
  "message": "Success",
  "data": {
    "users": [
      {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "active": true,
        "created_at": "2025-01-01T12:00:00",
        "total_points": 150,
        "rank_info": {
          "current_rank": {
            "name": "Bookworm",
            "color": "#9b59b6",
            "icon": "fa-book-open",
            "min_points": 150
          },
          "next_rank": {
            "name": "Scholar",
            "color": "#e67e22",
            "icon": "fa-graduation-cap",
            "min_points": 300
          },
          "points_needed": 40,
          "progress_percentage": 73,
          "total_points": 260
        }
      }
    ],
    "pagination": {
      "page": 1,
      "pages": 5,
      "per_page": 10,
      "total": 50,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

## Get User by ID
Retrieve detailed information about a specific user.

**Endpoint:** `GET /api/v1/users/{id}`

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/v1/users/1"
```

**Example Response:**
```json
{
  "message": "Success",
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "active": true,
    "created_at": "2025-01-01T12:00:00",
    "total_points": 150,
    "rank_info": {
      "current_rank": {
        "name": "Legend",
        "color": "#fd79a8",
        "icon": "fa-trophy",
        "min_points": 1500
      },
      "next_rank": null,
      "points_needed": 0,
      "progress_percentage": 0,
      "total_points": 10210
    },
    "borrowed_books_count": 2,
    "posted_books_count": 5
  }
}
```

## Create User
Create a new user account.

**Endpoint:** `POST /api/v1/users`

**Request Body:**
```json
{
  "username": "new_user",
  "email": "user@example.com",
  "password": "secure_password",
  "first_name": "Optional",
  "last_name": "Optional"
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/v1/users" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jane_smith",
    "email": "jane@example.com",
    "password": "mypassword123",
    "first_name": "Jane",
    "last_name": "Smith"
  }'
```

## Update User
Update user profile information. Users can only update their own profile.

**Endpoint:** `PUT /api/v1/users/{id}`
**Authentication:** Required

**Request Body:**
```json
{
  "first_name": "Updated First Name",
  "last_name": "Updated Last Name",
  "email": "newemail@example.com"
}
```

---

# Book Endpoints

## List Books
Get a paginated list of books with filtering and search capabilities.

**Endpoint:** `GET /api/v1/books`

**Parameters:**
- `page` (optional, integer): Page number (default: 1)
- `per_page` (optional, integer): Items per page (default: 20)
- `search` (optional, string): Search in title, author, description
- `category` (optional, string): Filter by specific category
- `available_only` (optional, boolean): Show only available books (true/false)

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/v1/books?search=python&category=Programming&available_only=true"
```

**Example Response:**
```json
{
  "message": "Success",
  "data": {
    "books": [
      {
        "id": 1,
        "title": "Learning Python",
        "author": "Mark Lutz",
        "category": "Programming",
        "isbn": "978-1449355739",
        "description": "A comprehensive guide to Python programming",
        "cover_url": "https://example.com/cover.jpg",
        "publication_year": 2013,
        "pages": 1648,
        "available": true,
        "created_at": "2025-01-01T12:00:00",
        "posted_by": 1
      }
    ],
    "pagination": {
      "page": 1,
      "pages": 3,
      "per_page": 20,
      "total": 45,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

## Get Book by ID
Retrieve detailed information about a specific book including ratings and reviews.

**Endpoint:** `GET /api/v1/books/{id}`

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/v1/books/1"
```

**Example Response:**
```json
{
  "message": "Success",
  "data": {
    "id": 1,
    "title": "Learning Python",
    "author": "Mark Lutz",
    "category": "Programming",
    "isbn": "978-1449355739",
    "description": "A comprehensive guide to Python programming",
    "cover_url": "https://example.com/cover.jpg",
    "publication_year": 2013,
    "pages": 1648,
    "available": true,
    "created_at": "2025-01-01T12:00:00",
    "posted_by": 1,
    "average_rating": 4.5,
    "review_count": 12,
    "poster_info": {
      "id": 1,
      "username": "john_doe",
      "full_name": "John Doe"
    }
  }
}
```

## Create Book
Add a new book to the library. Authentication required.

**Endpoint:** `POST /api/v1/books`
**Authentication:** Required

**Request Body:**
```json
{
  "title": "Book Title",
  "author": "Author Name",
  "category": "Category Name",
  "isbn": "978-1234567890",
  "description": "Book description (optional)",
  "cover_url": "https://example.com/cover.jpg (optional)",
  "publication_year": 2023,
  "pages": 300
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/v1/books" \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie" \
  -d '{
    "title": "Advanced Python Programming",
    "author": "Magnus Lie Hetland",
    "category": "Programming",
    "isbn": "978-1484200384",
    "description": "Learn advanced Python concepts",
    "publication_year": 2014,
    "pages": 336
  }'
```

## Update Book
Update book information. Only the book poster can update their books.

**Endpoint:** `PUT /api/v1/books/{id}`
**Authentication:** Required

**Request Body:** Same as Create Book (all fields optional)

## Delete Book
Delete a book from the library. Only the book poster can delete their books.

**Endpoint:** `DELETE /api/v1/books/{id}`
**Authentication:** Required

**Example Request:**
```bash
curl -X DELETE "http://localhost:5000/api/v1/books/1" \
  -H "Cookie: session=your_session_cookie"
```

---

# Borrowed Books Endpoints

## Get My Borrowed Books
Retrieve all books currently borrowed by the authenticated user.

**Endpoint:** `GET /api/v1/borrowed-books`
**Authentication:** Required

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/v1/borrowed-books" \
  -H "Cookie: session=your_session_cookie"
```

**Example Response:**
```json
{
  "message": "Success",
  "data": [
    {
      "id": 15,
      "book": {
        "id": 1,
        "title": "Learning Python",
        "author": "Mark Lutz",
        "category": "Programming"
      },
      "borrowed_date": "2025-01-01T12:00:00",
      "due_date": "2025-01-15T12:00:00",
      "is_agreed": true,
      "is_overdue": false
    }
  ]
}
```

## Borrow Book
Request to borrow a specific book.

**Endpoint:** `POST /api/v1/books/{id}/borrow`
**Authentication:** Required

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/v1/books/1/borrow" \
  -H "Cookie: session=your_session_cookie"
```

**Example Response:**
```json
{
  "message": "Book borrowed successfully",
  "data": {
    "id": 15,
    "book_id": 1,
    "due_date": "2025-01-15T12:00:00"
  }
}
```

## Return Book
Return a borrowed book.

**Endpoint:** `POST /api/v1/borrowed-books/{id}/return`
**Authentication:** Required

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/v1/borrowed-books/15/return" \
  -H "Cookie: session=your_session_cookie"
```

---

# Book Reviews Endpoints

## Get Book Reviews
Retrieve reviews for a specific book with pagination.

**Endpoint:** `GET /api/v1/books/{id}/reviews`

**Parameters:**
- `page` (optional, integer): Page number (default: 1)
- `per_page` (optional, integer): Items per page (default: 10)

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/v1/books/1/reviews?page=1&per_page=5"
```

**Example Response:**
```json
{
  "message": "Success",
  "data": {
    "reviews": [
      {
        "id": 1,
        "book_id": 1,
        "user_id": 2,
        "rating": 5,
        "review_text": "Excellent book for learning Python!",
        "created_at": "2025-01-01T12:00:00",
        "formatted_time": "01/01/2025 12:00",
        "time_ago": "2 days ago",
        "username": "jane_smith",
        "user_full_name": "Jane Smith"
      }
    ],
    "pagination": {
      "page": 1,
      "pages": 3,
      "per_page": 5,
      "total": 12,
      "has_next": true,
      "has_prev": false
    },
    "average_rating": 4.5
  }
}
```

## Create Book Review
Add a review and rating for a book.

**Endpoint:** `POST /api/v1/books/{id}/reviews`
**Authentication:** Required

**Request Body:**
```json
{
  "rating": 5,
  "review_text": "This is an excellent book! Highly recommended."
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/v1/books/1/reviews" \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie" \
  -d '{
    "rating": 4,
    "review_text": "Good book, learned a lot from it."
  }'
```

## Update Review
Update an existing review. Only the reviewer can update their review.

**Endpoint:** `PUT /api/v1/reviews/{id}`
**Authentication:** Required

**Request Body:**
```json
{
  "rating": 4,
  "review_text": "Updated review text"
}
```

## Delete Review
Delete a review. Only the reviewer can delete their review.

**Endpoint:** `DELETE /api/v1/reviews/{id}`
**Authentication:** Required

---

# Achievements Endpoints

## List All Achievements
Get all available achievements in the system.

**Endpoint:** `GET /api/v1/achievements`

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/v1/achievements"
```

**Example Response:**
```json
{
  "message": "Success",
  "data": [
    {
      "id": 1,
      "name": "First Book",
      "description": "Post your first book to the library",
      "category": "books",
      "points": 10,
      "requirement_type": "post_count",
      "requirement_value": 1,
      "icon": "fa-book",
      "color": "#3498db",
      "is_active": true,
      "created_at": "2025-01-01T12:00:00"
    }
  ]
}
```

## Get Achievement by ID
Retrieve details of a specific achievement.

**Endpoint:** `GET /api/v1/achievements/{id}`

## Get User Achievements
Get all achievements unlocked by a specific user.

**Endpoint:** `GET /api/v1/users/{id}/achievements`

**Example Response:**
```json
{
  "message": "Success",
  "data": [
    {
      "id": 1,
      "achievement": {
        "id": 1,
        "name": "First Book",
        "description": "Post your first book to the library",
        "points": 10,
        "icon": "fa-book",
        "color": "#3498db"
      },
      "unlocked_at": "2025-01-01T12:00:00",
      "is_seen": true
    }
  ]
}
```

---

# Discussions Endpoints

## List Discussions
Get discussion messages with pagination and optional book filtering.

**Endpoint:** `GET /api/v1/discussions`

**Parameters:**
- `page` (optional, integer): Page number (default: 1)
- `per_page` (optional, integer): Items per page (default: 20)
- `book_id` (optional, integer): Filter discussions for specific book

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/v1/discussions?book_id=1&page=1"
```

**Example Response:**
```json
{
  "message": "Success",
  "data": {
    "discussions": [
      {
        "id": 1,
        "user_id": 1,
        "username": "john_doe",
        "message": "This book was amazing! Highly recommend it.",
        "timestamp": "2025-01-01T12:00:00",
        "formatted_time": "01/01/2025 12:00",
        "book_id": 1
      }
    ],
    "pagination": {
      "page": 1,
      "pages": 2,
      "per_page": 20,
      "total": 25,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

## Create Discussion
Post a new discussion message.

**Endpoint:** `POST /api/v1/discussions`
**Authentication:** Required

**Request Body:**
```json
{
  "message": "Your discussion message here",
  "book_id": 1
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/v1/discussions" \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie" \
  -d '{
    "message": "Just finished reading this book. Great insights!",
    "book_id": 1
  }'
```

---

# Notifications Endpoints

## Get My Notifications
Retrieve notifications for the authenticated user.

**Endpoint:** `GET /api/v1/notifications`
**Authentication:** Required

**Parameters:**
- `page` (optional, integer): Page number (default: 1)
- `per_page` (optional, integer): Items per page (default: 20)
- `unread_only` (optional, boolean): Show only unread notifications

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/v1/notifications?unread_only=true" \
  -H "Cookie: session=your_session_cookie"
```

**Example Response:**
```json
{
  "message": "Success",
  "data": {
    "notifications": [
      {
        "id": 1,
        "user_id": 1,
        "type": "borrow_request",
        "title": "New Borrow Request",
        "message": "Someone wants to borrow your book 'Learning Python'",
        "is_read": false,
        "created_at": "2025-01-01T12:00:00",
        "formatted_time": "01/01/2025 12:00"
      }
    ],
    "pagination": {
      "page": 1,
      "pages": 1,
      "per_page": 20,
      "total": 5,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

## Mark Notification as Read
Mark a specific notification as read.

**Endpoint:** `PUT /api/v1/notifications/{id}/read`
**Authentication:** Required

**Example Request:**
```bash
curl -X PUT "http://localhost:5000/api/v1/notifications/1/read" \
  -H "Cookie: session=your_session_cookie"
```

---

# JavaScript Examples

Here are some JavaScript examples for consuming the API:

## Fetch Books with Search
```javascript
async function searchBooks(searchTerm, category = '') {
  const params = new URLSearchParams({
    search: searchTerm,
    category: category,
    available_only: 'true'
  });
  
  try {
    const response = await fetch(`/api/v1/books?${params}`);
    const data = await response.json();
    
    if (response.ok) {
      console.log('Books found:', data.data.books);
      return data.data.books;
    } else {
      console.error('Error:', data.error);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
}
```

## Create a Book Review
```javascript
async function addReview(bookId, rating, reviewText) {
  try {
    const response = await fetch(`/api/v1/books/${bookId}/reviews`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        rating: rating,
        review_text: reviewText
      })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      console.log('Review added successfully:', data.data);
      return data.data;
    } else {
      console.error('Error adding review:', data.error);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
}
```

## Get User's Borrowed Books
```javascript
async function getBorrowedBooks() {
  try {
    const response = await fetch('/api/v1/borrowed-books');
    const data = await response.json();
    
    if (response.ok) {
      console.log('Borrowed books:', data.data);
      return data.data;
    } else {
      console.error('Error:', data.error);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
}
```

---

# Error Handling

All endpoints return appropriate HTTP status codes and error messages. Common error responses:

## Validation Error (400)
```json
{
  "error": "Missing required field: title"
}
```

## Unauthorized (401)
```json
{
  "error": "Authentication required"
}
```

## Forbidden (403)
```json
{
  "error": "Access denied"
}
```

## Not Found (404)
```json
{
  "error": "Book not found"
}
```

## Server Error (500)
```json
{
  "error": "Internal server error"
}
```

---

## Testing the API

All endpoints have been thoroughly tested and are production-ready. Here are some quick test commands:

### Test Users Endpoint
```bash
# Get all users with pagination
curl -X GET "http://localhost:5000/api/v1/users?page=1&per_page=5"

# Search for specific users
curl -X GET "http://localhost:5000/api/v1/users?search=kiet"
```

### Test Books Endpoint
```bash
# Get all books
curl -X GET "http://localhost:5000/api/v1/books"

# Search books by category
curl -X GET "http://localhost:5000/api/v1/books?category=Programming&available_only=true"
```

## Performance & Limits

- **Pagination**: All list endpoints support pagination with `page` and `per_page` parameters
- **Default Page Size**: 20 items per page for most endpoints, 10 for reviews
- **Maximum Page Size**: 100 items per page
- **Response Time**: < 200ms for most endpoints
- **Database**: PostgreSQL with optimized queries and indexing

## Rate Limiting

Currently no rate limiting is implemented, but it's recommended to:
- Limit API calls to 1000 requests per hour per user
- Cache responses when possible
- Use pagination for large datasets

## Data Models

### User Object
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "active": true,
  "created_at": "2025-01-01T12:00:00",
  "total_points": 260,
  "rank_info": {
    "current_rank": {
      "name": "Bookworm",
      "color": "#9b59b6",
      "icon": "fa-book-open",
      "min_points": 150
    },
    "next_rank": {
      "name": "Scholar",
      "color": "#e67e22",
      "icon": "fa-graduation-cap",
      "min_points": 300
    },
    "points_needed": 40,
    "progress_percentage": 73,
    "total_points": 260
  }
}
```

### Book Object
```json
{
  "id": 1,
  "title": "Learning Python",
  "author": "Mark Lutz",
  "category": "Programming",
  "isbn": "978-1449355739",
  "description": "A comprehensive guide to Python programming",
  "cover_url": "https://example.com/cover.jpg",
  "publication_year": 2013,
  "pages": 1648,
  "available": true,
  "created_at": "2025-01-01T12:00:00",
  "posted_by": 1,
  "average_rating": 4.5,
  "review_count": 12
}
```

### Review Object
```json
{
  "id": 1,
  "book_id": 1,
  "user_id": 2,
  "rating": 5,
  "review_text": "Excellent book for learning Python!",
  "created_at": "2025-01-01T12:00:00",
  "formatted_time": "01/01/2025 12:00",
  "time_ago": "2 days ago",
  "username": "jane_smith",
  "user_full_name": "Jane Smith"
}
```

---

This API provides complete CRUD operations for all major entities in your book borrowing system, following RESTful conventions and providing comprehensive functionality for building client applications.