# L.E.A.F - Digital Book Borrowing System

## Overview

LibraryApp is a web-based digital library management system built with Flask that allows users to browse, search, and borrow books from a digital catalog. The application uses a simple JSON-based data store for books and Flask sessions for user state management, making it lightweight and easy to deploy.

## System Architecture

### Frontend Architecture
- **Framework**: HTML templates with Jinja2 templating engine
- **CSS Framework**: Bootstrap 5 with Replit dark theme
- **Icons**: Font Awesome 6.4.0
- **JavaScript**: Vanilla JavaScript for interactive features
- **Responsive Design**: Mobile-first approach using Bootstrap's grid system

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: PostgreSQL with Flask-SQLAlchemy ORM
- **Session Management**: Flask sessions for user state and session-based borrowing tracking
- **Data Storage**: Database tables for books and borrowing records
- **Logging**: Python's built-in logging module
- **Architecture Pattern**: MVC (Model-View-Controller) pattern

### Key Design Decisions
- **Database-driven**: Migrated from JSON to PostgreSQL for persistence and scalability
- **Session-based borrowing**: Uses session IDs to track borrowed books without user accounts
- **ORM Integration**: SQLAlchemy models for Book and BorrowedBook entities
- **Data persistence**: All borrowing records and book catalog stored in database

## Key Components

### Core Application Files
- **`app.py`**: Main Flask application with all routes and business logic
- **`main.py`**: Entry point for running the application
- **`models.py`**: SQLAlchemy database models for Book and BorrowedBook

### Templates
- **`base.html`**: Base template with navigation and common layout
- **`index.html`**: Book catalog browsing and search interface
- **`book_detail.html`**: Individual book details and borrowing interface
- **`dashboard.html`**: User's borrowed books management

### Static Assets
- **`static/css/style.css`**: Custom styling for book covers and cards
- **`static/js/main.js`**: Client-side JavaScript for interactivity

### Core Functions
- **`load_books()`**: Loads book data from PostgreSQL database
- **`get_book_by_id()`**: Retrieves specific book information from database
- **`get_borrowed_books()`**: Manages borrowed books using session IDs and database records
- **`add_borrowed_book()`**: Handles book borrowing with database persistence and due date tracking
- **`remove_borrowed_book()`**: Manages book returns by updating database records
- **`get_session_id()`**: Generates unique session identifiers for borrowing tracking

## Data Flow

1. **Book Browsing**: Users access the catalog through the index route, which loads books from PostgreSQL and applies search/filter criteria
2. **Book Details**: Individual book pages show detailed information and borrowing options
3. **Borrowing Process**: When a user borrows a book, a record is created in the borrowed_books table with session ID and 2-week due date
4. **Dashboard**: Users can view their borrowed books, due dates, and overdue status from database records
5. **Session Persistence**: Session IDs track borrowing state across requests, with all data persisted in database

## External Dependencies

### Python Packages
- **Flask**: Web framework for routing and templating
- **Standard Library**: `os`, `json`, `logging`, `datetime` for core functionality

### Frontend Libraries
- **Bootstrap 5**: UI framework with Replit dark theme customization
- **Font Awesome 6.4.0**: Icon library for UI elements
- **Open Library**: Book cover images via covers.openlibrary.org API

### External Services
- **Open Library Covers API**: Provides book cover images based on ISBN

## Deployment Strategy

### Current Setup
- **Host**: 0.0.0.0 (all interfaces)
- **Port**: 5000
- **Debug Mode**: Enabled for development
- **Session Secret**: Environment variable with fallback to development key

### Environment Configuration
- **SESSION_SECRET**: Environment variable for session security
- **Development Mode**: Debug enabled for local development
- **Static File Serving**: Flask's built-in static file serving

### Deployment Considerations
- Application is designed for single-instance deployment
- No database setup required - uses JSON file storage
- Session data is stored in memory (not persistent across restarts)
- Book catalog is loaded from file system on each request

## Changelog

- June 29, 2025: Initial setup with JSON-based book storage
- June 29, 2025: **Database Migration** - Migrated from JSON file storage to PostgreSQL database
  - Added SQLAlchemy models for Book and BorrowedBook entities
  - Implemented session-based borrowing tracking with database persistence
  - Added admin routes for book management and data seeding
  - Updated all data access functions to use database queries
  - Maintained backward compatibility of existing UI and functionality
- June 29, 2025: **Social Features Implementation**
  - Added Discussion system with real-time chat functionality
  - Created Notifications system for book borrowing alerts
  - Implemented "View Poster" functionality with user profiles
  - Built private messaging system between users
  - Added book posting tracking to identify poster ownership
- June 29, 2025: **UI/UX Redesign** 
  - Redesigned navigation from horizontal navbar to clean sidebar layout
  - Organized navigation into logical sections (Browse, Community, Quick Actions)
  - Implemented glassmorphism design throughout the interface
  - Added responsive mobile support and improved accessibility
- June 29, 2025: **Timezone Enhancement**
  - Added Vietnam timezone (UTC+7) display for discussion timestamps
  - Updated Discussion model to show localized time format (dd/mm/yyyy HH:MM)
- June 29, 2025: **Authentication Requirements Implementation**
  - Enforced user authentication for all book borrowing and returning operations
  - Required login for posting new books to the catalog
  - Updated UI to show login prompts instead of borrow buttons for unauthenticated users
  - Removed guest user functionality - all real book operations now require user accounts
  - Updated navigation to hide authenticated-only features for guest users
- June 30, 2025: **Comprehensive UI/UX Responsive Design Overhaul**
  - Implemented mobile-first responsive design with breakpoints for all screen sizes
  - Enhanced book catalog grid with adaptive column layouts (4 columns on XL, 3 on LG, 2 on SM, 1 on mobile)
  - Improved navigation bar with mobile-optimized layout and collapsible elements
  - Added mobile notification and borrowed count indicators in navbar
  - Enhanced search and filter forms with better mobile UX and touch-friendly inputs
  - Implemented responsive button layouts with proper text truncation and spacing
  - Added sticky positioning controls for better mobile experience
  - Enhanced glassmorphism design with improved dropdown styling and accessibility
  - Optimized text formatting with proper wrapping and overflow handling
  - Improved sidebar responsiveness with dynamic width calculations
  - Added loading states and focus indicators for better accessibility
  - Enhanced action button layouts with flexible grid systems for all screen sizes
- June 30, 2025: **"Talk to Author" Feature Implementation**
  - Added "Talk to Author" buttons on book detail pages and catalog cards
  - Integrated with existing private messaging system for direct author communication
  - Enhanced private chat interface to show book context when conversation starts from a book page
  - Implemented book-specific conversation routing with contextual information display
  - Added responsive design for book context cards in chat interface
  - Fixed database schema issues with missing borrowed_books columns (agreed_due_date, is_agreed)
- July 6, 2025: **Ratings and Reviews System Implementation**
  - Added BookReview model with 1-5 star rating system and review text
  - Implemented unique constraint to prevent duplicate reviews from same user  
  - Added rating display to book catalog cards with average rating and review count
  - Built comprehensive review interface on book detail pages with interactive star rating
  - Created review submission, editing, and deletion functionality with proper user authentication
  - Added JavaScript-powered rating displays with loading animations and error handling
  - Integrated glassmorphism styling for review cards and rating interface components
- July 6, 2025: **Achievements System Implementation**
  - Added Achievement and UserAchievement models with comprehensive tracking system
  - Implemented 10 different achievement types across books, reviews, social, and special categories
  - Created automatic achievement checking and awarding on book borrow/return actions
  - Built beautiful achievements page with progress tracking and category filtering
  - Added achievement notifications with animated modals for real-time unlocking feedback
  - Integrated achievements into navigation with trophy icons and user dashboard
  - Created seeding system for initial achievement data with points and requirements
- July 6, 2025: **User Ranking System Implementation**
  - Added comprehensive 8-tier ranking system based on achievement points (Newbie to Legend)
  - Implemented User.get_total_points() and User.get_rank_info() methods for dynamic rank calculation
  - Created dedicated ranks page with current rank display, all rank tiers, and top 10 leaderboard
  - Added rank display to sidebar user profile with progress bars and points needed for next rank
  - Integrated rank badges in poster profiles and achievements page for comprehensive rank visibility
  - Built responsive rank progression system with color-coded tiers and unique icons for each rank
- July 7, 2025: **Profile Customization System on Poster Pages**
  - Integrated profile customization modal directly into poster profile pages
  - Added "Customize Profile" button that appears only when viewing your own profile
  - Implemented real-time preview of banner and title customizations
  - Created comprehensive banner selection with 6 gradient styles (free to 150 points)
  - Added custom title system with 7 color options and 30-character limit
  - Built cost calculation system with point validation and remaining points display
  - Enhanced poster profile headers to display custom banners and titles
  - Added UserProfile model integration for persistent storage of customizations
- July 13, 2025: **MVC Architecture Refactor and Model Organization**
  - Implemented full MVC pattern with separate controllers, models, and views directories
  - Split monolithic app.py into focused controller files for better maintainability
  - Created separate model files for logical separation (user.py, book.py, social.py, review.py, achievement.py)
  - Implemented application factory pattern in config.py for better configuration management
  - Updated all imports and dependencies to work with new modular structure
  - Maintained all existing functionality while improving code organization and scalability
  - Enhanced project structure following Flask best practices for enterprise applications
- July 13, 2025: **Achievement System Integration and Points Awarding**
  - Fixed achievement system to automatically award points for book posting, borrowing, returning, and reviewing
  - Added achievement notifications with trophy emojis and points display in flash messages
  - Integrated achievement checking in all major user actions (post_book, borrow_book, return_book, add_review)
  - Created special dev testing achievement (10,000 points) for development testing purposes
  - Fixed database schema references from recipient_user_id to user_id in notifications
  - Removed duplicate add_book function and cleaned up controller code structure
- July 27, 2025: **Dual Navigation System Implementation**
  - Added comprehensive top navigation bar with glassmorphism styling alongside existing sidebar
  - Implemented responsive design with mobile-optimized collapsible menu
  - Created synchronized notification badges between navbar and sidebar
  - Added user dropdown with profile, rank, points display, and logout functionality
  - Integrated community dropdown with Discussion, Achievements, and Ranks access
  - Built login/signup authentication templates with form validation and glassmorphism design
  - Added borrowed book count display in both navigation systems with animation
  - Configured sidebar toggle button to only appear on small screens (mobile/tablet)
- August 10, 2025: **Forum and Leaderboard Enhancements**
  - Fixed "405 method not allowed" error in forum/discussion by adding POST method support
  - Implemented scrollable leaderboard showing only top 20 users with 400px fixed height
  - Added custom scrollbar styling with glassmorphism design for leaderboard
  - Updated points guide in ranks page to show specific point values for each activity
  - Achievement points system: Borrow Books (15), Reviews (5), Discussion (1 per 5 messages), Post Books (20)

## User Preferences

Preferred communication style: Simple, everyday language.
Timezone preference: Vietnam timezone (UTC+7) for all timestamps.