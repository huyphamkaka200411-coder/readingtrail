# L.E.A.F - Digital Book Borrowing System

## Overview
L.E.A.F is a web-based digital library management system built with Flask that enables users to browse, search, borrow, and review books from a digital catalog. It aims to provide a comprehensive, interactive platform for book enthusiasts, incorporating social features like discussions, private messaging, user profiles, and an achievement/ranking system to foster community engagement. The project's ambition is to deliver a lightweight, scalable, and user-friendly digital library experience with a strong focus on community interaction.

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
- **Database**: PostgreSQL with Flask-SQLAlchemy ORM for persistent storage of books, borrowing records, user data, reviews, achievements, and social interactions.
- **Session Management**: Flask sessions used for user state and temporary borrowing tracking.
- **Architecture Pattern**: Refactored to a modular MVC (Model-View-Controller) pattern with separate files for models and controllers.
- **Logging**: Python's built-in logging module.

### Feature Specifications
- **Book Management**: Browsing, searching, detailed views, and borrowing/returning of books.
- **User Authentication**: Required for all borrowing, posting, and social interactions.
- **Social Features**:
    - **Discussions**: Real-time chat functionality.
    - **Private Messaging**: Direct user-to-user communication, including "Talk to Author" from book pages.
    - **User Profiles**: Customizable profiles with banners and titles, displaying user activity, ranks, and achievements.
- **Ratings & Reviews**: 1-5 star rating system with text reviews, displayed on book cards and detail pages.
- **Achievements & Ranking**:
    - **Achievements**: System to track and award achievements for various user actions (borrowing, reviewing, posting, etc.).
    - **Ranking**: 8-tier ranking system based on achievement points, with a dedicated ranks page and leaderboard.

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