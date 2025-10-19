
let isLoading = false;

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    console.log('ReadingTrail initialized');
    updateBorrowedCount();
    updateNotificationCount();
    loadCatalogRatings();
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;
    
    const alertId = 'alert-' + Date.now();
    const alertHTML = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="fas fa-${getAlertIcon(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    alertContainer.insertAdjacentHTML('beforeend', alertHTML);
    
    setTimeout(() => {
        const alertElement = document.getElementById(alertId);
        if (alertElement) {
            const alert = new bootstrap.Alert(alertElement);
            alert.close();
        }
    }, 5000);
}
function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function setButtonLoading(button, loading = true) {
    if (loading) {
        button.classList.add('loading');
        button.disabled = true;
    } else {
        button.classList.remove('loading');
        button.disabled = false;
    }
}

// Borrow book function
async function borrowBook(bookId, bookTitle, buttonElement) {
    if (isLoading) return;
    
    isLoading = true;
    setButtonLoading(buttonElement, true);
    
    try {
        const response = await fetch(`/borrow/${bookId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            
            // Check for new achievements
            if (data.new_achievements && data.new_achievements.length > 0) {
                showAchievementNotifications(data.new_achievements);
            }
            
            // Update button state
            buttonElement.innerHTML = '<i class="fas fa-undo me-1"></i>Trả sách';
            buttonElement.className = 'btn btn-warning return-btn';
            buttonElement.classList.remove('borrow-btn');
            buttonElement.classList.add('return-btn');
            
            // Update event listener
            buttonElement.removeEventListener('click', borrowBook);
            buttonElement.addEventListener('click', function() {
                returnBook(bookId, bookTitle, this);
            });
            
            // Update borrowed count
            updateBorrowedCount(1);
            
            // Add borrowed badge if on catalog page
            addBorrowedBadge(buttonElement);
            
        } else {
            showAlert(data.message, 'danger');
        }
        
    } catch (error) {
        console.error('Error borrowing book:', error);
        console.error('Response status:', response?.status);
        console.error('Response text:', await response?.text());
        showAlert('Không thể mượn sách. Vui lòng thử lại.', 'danger');
    } finally {
        isLoading = false;
        setButtonLoading(buttonElement, false);
    }
}

// Return book function
async function returnBook(bookId, bookTitle, buttonElement) {
    if (isLoading) return;
    
    isLoading = true;
    setButtonLoading(buttonElement, true);
    
    try {
        const response = await fetch(`/return/${bookId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            
            // Check for new achievements
            if (data.new_achievements && data.new_achievements.length > 0) {
                showAchievementNotifications(data.new_achievements);
            }
            
            // Check if we're on the dashboard page
            if (window.location.pathname === '/dashboard') {
                // Remove the card from dashboard
                const card = buttonElement.closest('.col-lg-6, .col-xl-4');
                if (card) {
                    card.style.animation = 'fadeOut 0.3s ease-out';
                    setTimeout(() => {
                        card.remove();
                        // Check if no books remain
                        const remainingCards = document.querySelectorAll('.return-btn').length;
                        if (remainingCards <= 1) {
                            setTimeout(() => location.reload(), 500);
                        }
                    }, 300);
                }
            } else {
                // Update button state for catalog/detail pages
                buttonElement.innerHTML = '<i class="fas fa-download me-1"></i>Mượn ngay';
                buttonElement.className = 'btn btn-success borrow-btn';
                buttonElement.classList.remove('return-btn');
                buttonElement.classList.add('borrow-btn');
                
                // Update event listener
                buttonElement.removeEventListener('click', returnBook);
                buttonElement.addEventListener('click', function() {
                    borrowBook(bookId, bookTitle, this);
                });
                
                // Remove borrowed badge
                removeBorrowedBadge(buttonElement);
            }
            
            // Update borrowed count
            updateBorrowedCount(-1);
            
        } else {
            showAlert(data.message, 'danger');
        }
        
    } catch (error) {
        console.error('Error returning book:', error);
        showAlert('Không thể trả sách. Vui lòng thử lại.', 'danger');
    } finally {
        isLoading = false;
        setButtonLoading(buttonElement, false);
    }
}

// Update borrowed count in sidebar
function updateBorrowedCount(change = 0) {
    const sidebarCountElement = document.getElementById('sidebar-borrowed-count');
    const navbarCountElement = document.getElementById('navbar-borrowed-count');
    
    if (sidebarCountElement) {
        const currentCount = parseInt(sidebarCountElement.textContent) || 0;
        const newCount = Math.max(0, currentCount + change);
        sidebarCountElement.textContent = newCount;
        
        // Add animation
        sidebarCountElement.style.transform = 'scale(1.2)';
        setTimeout(() => {
            sidebarCountElement.style.transform = 'scale(1)';
        }, 200);
    }
    
    // Update navbar count as well
    if (navbarCountElement) {
        const currentCount = parseInt(navbarCountElement.textContent) || 0;
        const newCount = Math.max(0, currentCount + change);
        navbarCountElement.textContent = newCount;
        
        // Add animation
        navbarCountElement.style.transform = 'scale(1.2)';
        setTimeout(() => {
            navbarCountElement.style.transform = 'scale(1)';
        }, 200);
    }
}

// Update notification count in both sidebar and navbar
function updateNotificationCount() {
    fetch('/api/notifications/count')
        .then(response => response.json())
        .then(data => {
            const unreadCount = data.data?.unread_count ?? 0;
            
            // Update sidebar badge
            const sidebarBadge = document.getElementById('sidebar-notification-badge');
            if (sidebarBadge) {
                if (count > 0) {
                    sidebarBadge.textContent = count;
                    sidebarBadge.style.display = 'inline';
                } else {
                    sidebarBadge.style.display = 'none';
                }
            }
            
            // Update navbar badge
            const navbarBadge = document.getElementById('navbar-notification-badge');
            if (navbarBadge) {
                if (count > 0) {
                    navbarBadge.textContent = count;
                    navbarBadge.style.display = 'inline';
                } else {
                    navbarBadge.style.display = 'none';
                }
            }
        })
        .catch(error => {
            console.error('Error updating notification count:', error);
        });
}

// Add borrowed badge to book card
function addBorrowedBadge(buttonElement) {
    const card = buttonElement.closest('.card');
    if (card) {
        const coverContainer = card.querySelector('.book-cover-container, .book-cover-container-large');
        if (coverContainer && !coverContainer.querySelector('.badge')) {
            const badge = document.createElement('div');
            badge.className = 'position-absolute top-0 end-0 m-2';
            badge.innerHTML = '<span class="badge bg-success"><i class="fas fa-check me-1"></i>Đã mượn</span>';
            coverContainer.appendChild(badge);
        }
    }
}

// Remove borrowed badge from book card
function removeBorrowedBadge(buttonElement) {
    const card = buttonElement.closest('.card');
    if (card) {
        const badge = card.querySelector('.position-absolute.top-0.end-0');
        if (badge) {
            badge.remove();
        }
    }
}

// Smooth scroll to top
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Add CSS for fade out animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; transform: scale(1); }
        to { opacity: 0; transform: scale(0.9); }
    }
`;
document.head.appendChild(style);

// Handle search form submission with loading state
document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.querySelector('form[action*="index"]');
    if (searchForm) {
        searchForm.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                setButtonLoading(submitButton, true);
            }
        });
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[name="search"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to clear search
    if (e.key === 'Escape') {
        const searchInput = document.querySelector('input[name="search"]');
        if (searchInput && searchInput === document.activeElement && searchInput.value) {
            searchInput.value = '';
        }
    }
});

// Image lazy loading fallback for older browsers
document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for older browsers
        images.forEach(img => {
            img.src = img.dataset.src;
        });
    }
});

// Borrow book with optional due date
function borrowBookWithDueDate(bookId, bookTitle, button, proposedDueDate = null) {
    if (isLoading) return;
    
    isLoading = true;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Đang xử lý...';
    button.disabled = true;
    
    const requestData = proposedDueDate ? { proposed_due_date: proposedDueDate } : {};
    
    fetch(`/borrow/${bookId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', data.message);
            
            // Update UI based on response
            if (proposedDueDate) {
                button.innerHTML = '<i class="fas fa-clock me-1"></i>Chờ duyệt';
                button.classList.remove('btn-success');
                button.classList.add('btn-warning');
            } else {
                // Replace with return button for auto-approved books
                button.innerHTML = '<i class="fas fa-undo me-1"></i>Trả sách';
                button.classList.remove('btn-success', 'borrow-btn');
                button.classList.add('btn-warning', 'return-btn');
                button.dataset.bookId = bookId;
                button.dataset.bookTitle = bookTitle;
                
                // Update borrowed count
                updateBorrowedCount();
            }
        } else {
            showAlert('danger', data.message);
            button.innerHTML = originalText;
            button.disabled = false;
        }
    })
    .catch(error => {
        showAlert('danger', 'Có lỗi xảy ra khi xử lý yêu cầu.');
        button.innerHTML = originalText;
        button.disabled = false;
    })
    .finally(() => {
        isLoading = false;
    });
}

// Export functions for global use
window.borrowBook = borrowBook;
window.borrowBookWithDueDate = borrowBookWithDueDate;
window.returnBook = returnBook;
window.showAlert = showAlert;

// Rating system functions
function renderStarsSmall(rating, maxStars = 5) {
    let starsHtml = '';
    // Show both filled and empty stars to complete the rating display
    for (let i = 1; i <= maxStars; i++) {
        if (i <= rating) {
            starsHtml += '<span class="star">★</span>';
        } else {
            starsHtml += '<span class="star empty">★</span>';
        }
    }
    return starsHtml;
}

function loadCatalogRatings() {
    // Get all rating display elements
    const ratingDisplays = document.querySelectorAll('.rating-display');
    
    ratingDisplays.forEach(display => {
        const bookId = display.getAttribute('data-book-id');
        if (bookId) {
            loadBookRating(bookId);
        }
    });
}

function loadBookRating(bookId) {
    fetch(`/api/books/${bookId}/reviews`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                updateBookRatingDisplay(bookId, data.reviews);
            } else {
                hideRatingDisplay(bookId);
            }
        })
        .catch(error => {
            hideRatingDisplay(bookId);
        });
}

function updateBookRatingDisplay(bookId, reviews) {
    const starsElement = document.getElementById(`stars-${bookId}`);
    const textElement = document.getElementById(`rating-text-${bookId}`);
    const displayElement = document.querySelector(`[data-book-id="${bookId}"]`);
    
    if (!starsElement || !textElement || !displayElement) {
        return;
    }
    
    if (reviews.length === 0) {
        // Hide rating display for books with no reviews
        hideRatingDisplay(bookId);
        return;
    }
    
    const totalRating = reviews.reduce((sum, review) => sum + review.rating, 0);
    const averageRating = totalRating / reviews.length;
    const roundedRating = Math.round(averageRating * 10) / 10;
    
    starsElement.innerHTML = renderStarsSmall(Math.round(averageRating));
    textElement.textContent = `${roundedRating} (${reviews.length})`;
    
    // Show the rating display with animation
    displayElement.classList.add('loaded');
}

function hideRatingDisplay(bookId) {
    const displayElement = document.querySelector(`[data-book-id="${bookId}"]`);
    if (displayElement) {
        displayElement.style.display = 'none';
    }
}

// Achievement notification functions
function showAchievementNotifications(achievements) {
    achievements.forEach((achievement, index) => {
        setTimeout(() => {
            showAchievementModal(achievement);
        }, index * 500); // Stagger notifications
    });
}

function showAchievementModal(achievement) {
    // Create achievement modal
    const modalId = 'achievementModal-' + Date.now();
    const modalHTML = `
        <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content achievement-modal">
                    <div class="modal-body text-center p-4">
                        <div class="achievement-icon-large mb-3">
                            <i class="fas ${achievement.icon}"></i>
                        </div>
                        <h3 class="achievement-title mb-2">Đạt thành tích!</h3>
                        <h4 class="achievement-name mb-3">${achievement.name}</h4>
                        <p class="achievement-description mb-3">${achievement.description}</p>
                        <div class="achievement-points">
                            <i class="fas fa-star"></i>
                            +${achievement.points} điểm
                        </div>
                        <button type="button" class="btn btn-primary mt-3" data-bs-dismiss="modal">
                            <i class="fas fa-trophy me-2"></i>Tuyệt vời!
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();
    
    // Remove modal from DOM after it's hidden
    document.getElementById(modalId).addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Add CSS for achievement modal
const achievementStyles = `
<style>
.achievement-modal .modal-content {
    background: linear-gradient(135deg, #f39c12, #e67e22);
    color: white;
    border: none;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.achievement-icon-large {
    width: 80px;
    height: 80px;
    margin: 0 auto;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.5rem;
    animation: bounceIn 0.6s ease-out;
}

.achievement-title {
    font-size: 1.5rem;
    font-weight: 600;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.achievement-name {
    font-size: 1.3rem;
    font-weight: 700;
    color: #fff;
}

.achievement-description {
    font-size: 1rem;
    opacity: 0.9;
}

.achievement-points {
    font-size: 1.2rem;
    font-weight: 600;
    background: rgba(255, 255, 255, 0.2);
    padding: 10px 20px;
    border-radius: 20px;
    display: inline-block;
}

@keyframes bounceIn {
    0% {
        transform: scale(0.3);
        opacity: 0;
    }
    50% {
        transform: scale(1.05);
    }
    70% {
        transform: scale(0.9);
    }
    100% {
        transform: scale(1);
        opacity: 1;
    }
}
</style>
`;

// Add styles to head if not already added
if (!document.querySelector('#achievement-styles')) {
    const styleElement = document.createElement('div');
    styleElement.id = 'achievement-styles';
    styleElement.innerHTML = achievementStyles;
    document.head.appendChild(styleElement);
}

// Cancel borrow request function
async function cancelBorrowRequest(bookId) {
    if (!confirm('Bạn có chắc muốn hủy yêu cầu mượn sách?')) {
        return;
    }
    
    try {
        const response = await fetch(`/cancel_borrow_request/${bookId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            // Reload the page to update the dashboard
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showAlert(data.message || 'Không thể hủy yêu cầu', 'error');
        }
    } catch (error) {
        console.error('Error cancelling request:', error);
        showAlert('Lỗi khi hủy yêu cầu', 'error');
    }
}
