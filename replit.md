# ReadingTrail - Digital Book Borrowing System

## Overview
ReadingTrail is a web-based digital library management system built with Flask that enables users to browse, search, borrow, and review books from a digital catalog. The system focuses on core library features with social interactions, providing a simple and clean user experience for book management, borrowing, reviews, discussions, and private messaging.

## Recent Changes (October 2025)
- **Complete Gamification Removal (Oct 9)**: Eliminated all gamification features to focus on core library functionality:
  - Removed Achievement system (models, controllers, routes, API endpoints, and all database references)
  - Removed Ranking system (8-tier rank structure, points calculation, leaderboards)
  - Removed UserProfile model and profile customization features (banners, custom titles)
  - Deleted all achievement-related templates (achievements.html, achievements_guide.html, ranks.html, profile.html)
  - Cleaned up all achievement/ranking references from controllers (book_controller.py, review_controller.py, social_controller.py, api_controller.py)
  - Removed view_poster route and function as profile pages no longer exist
  - Removed gamification fields (total_points, rank_info) from User API responses
  - App now focuses exclusively on: book management, borrowing/returning, reviews, discussions, and private messaging

- **Additional UI Cleanup (Oct 9)**: Further simplification of user interface:
  - Installed pytz package to fix timezone handling in private chat feature
  - Removed "Xem người đăng" (view poster) button from book detail pages
  - Replaced "Trả sách" (return book) button with status message on book detail pages
  - Removed mark-as-read functionality from notifications (removed checkmark buttons and "Đánh dấu đã đọc tất cả" button)
  - Notifications now display without read/unread states - cleaner, simpler interface

- **UI Simplification (Oct 9)**: Major cleanup to streamline user interface:
  - Removed "Đã mượn" (borrowed count) display from navbar, sidebar, and profile page
  - Replaced complex background customization with simple dark/light mode toggle using localStorage and Bootstrap's data-bs-theme
  - Completely removed PowerUp shop feature (models, controllers, templates, routes, and all references)
  - Simplified achievements page - removed category filters, displaying all achievements in a single consolidated list
  - Fixed notification endpoint bug (updated main.js to use /api/notifications/count consistently)

- **Vietnamese Conversion Completed**: Removed all translation infrastructure (controllers, routes, JSON data files) and converted all user-facing content to Vietnamese-only. This includes:
  - All templates (base.html, index.html, authentication templates, book templates)
  - JavaScript alerts and messages (static/js/main.js)
  - Form labels, buttons, navigation elements
  - Category dropdown options (English values preserved for data integrity, Vietnamese labels displayed via mapping)
  - Image fallback text and status messages
  - Added category_vn mapping dictionaries in templates to display Vietnamese category names while preserving English database values

## User Preferences
Preferred communication style: Simple, everyday language.
Timezone preference: Vietnam timezone (UTC+7) for all timestamps.

## System Architecture

### UI/UX Decisions
- **Design System**: Glassmorphism aesthetic for a modern, sleek look.
- **Theming**: Bootstrap 5 with a Replit dark theme.
- **Responsiveness**: Mobile-first approach with comprehensive responsive design across all screen sizes.
- **Navigation**: Dual navigation system with a responsive top navbar and a sidebar, synchronized for consistency.
- **Language**: All content is in Vietnamese.

### Technical Implementations
- **Backend Framework**: Flask (Python web framework).
- **Database**: PostgreSQL with Flask-SQLAlchemy ORM for persistent storage of books, borrowing records, user data, reviews, and social interactions.
- **Session Management**: Flask sessions used for user state and temporary borrowing tracking.
- **Architecture Pattern**: Refactored to a modular MVC (Model-View-Controller) pattern with separate files for models and controllers.
- **Logging**: Python's built-in logging module.

### Feature Specifications
- **Book Management**: Browsing, searching, detailed views, and borrowing/returning of books.
- **User Authentication**: Required for all borrowing, posting, and social interactions.
- **Social Features**:
    - **Discussions**: Real-time chat functionality for general discussions and book-specific conversations.
    - **Private Messaging**: Direct user-to-user communication, including "Talk to Author" from book pages.
- **Ratings & Reviews**: 1-5 star rating system with text reviews, displayed on book cards and detail pages.

### System Design Choices
- **Database-driven**: All core data is persisted in a PostgreSQL database for scalability and reliability.
- **Modular Codebase**: Application factory pattern and MVC structure for improved maintainability and scalability.
- **Dynamic Content**: Jinja2 templating engine for rendering dynamic content.

## External Dependencies

### Python Packages
- **Flask**: Core web framework.
- **Flask-SQLAlchemy**: ORM for PostgreSQL database interaction.
- **Standard Library**: `os`, `json`, `logging`, `datetime`.

### Frontend Libraries
- **Bootstrap 5**: UI framework.
- **Font Awesome 6.4.0**: Icon library.
- **Vanilla JavaScript**: For interactive features.

### External Services
- **Open Library Covers API**: Used to fetch book cover images (via `covers.openlibrary.org`).