/**
 * Animations Module
 * Handles UI animations: completion, swipe-to-delete, transitions
 */

const Animations = (function() {
    'use strict';

    /**
     * Animate reminder completion
     * Sequence: checkbox checked → fade out → slide up → remove from DOM
     */
    async function animateCompletion(cardElement) {
        return new Promise((resolve) => {
            // Step 1: Add completing class
            cardElement.classList.add('completing');

            // Step 2: Fade out (250ms)
            setTimeout(() => {
                cardElement.classList.add('fade-out');
            }, 100);

            // Step 3: Slide up (250ms)
            setTimeout(() => {
                cardElement.classList.add('slide-up');
            }, 350);

            // Step 4: Remove from DOM
            setTimeout(() => {
                cardElement.remove();
                resolve();
            }, 600);
        });
    }

    /**
     * Setup swipe-to-delete gesture for reminder cards
     */
    function setupSwipeToDelete(cardElement, onDelete) {
        let startX = 0;
        let currentX = 0;
        let isSwiping = false;

        // Touch start
        cardElement.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            currentX = startX;
            isSwiping = true;
            cardElement.classList.add('swiping');
        }, { passive: true });

        // Touch move
        cardElement.addEventListener('touchmove', (e) => {
            if (!isSwiping) return;

            currentX = e.touches[0].clientX;
            const diff = currentX - startX;

            // Only allow left swipe
            if (diff < 0) {
                const translateX = Math.max(diff, -80);
                cardElement.style.transform = `translateX(${translateX}px)`;

                // Show delete action when swiped enough
                if (Math.abs(diff) > 40) {
                    cardElement.classList.add('swipe-left');
                } else {
                    cardElement.classList.remove('swipe-left');
                }
            }
        }, { passive: true });

        // Touch end
        cardElement.addEventListener('touchend', async () => {
            if (!isSwiping) return;

            const diff = currentX - startX;
            cardElement.classList.remove('swiping');

            // If swiped far enough, delete
            if (Math.abs(diff) > 80) {
                cardElement.style.transform = 'translateX(-100%)';
                cardElement.style.opacity = '0';

                if (onDelete && typeof onDelete === 'function') {
                    await onDelete();
                }

                setTimeout(() => {
                    cardElement.remove();
                }, 300);
            } else {
                // Snap back
                cardElement.style.transform = '';
                cardElement.classList.remove('swipe-left');
            }

            isSwiping = false;
            startX = 0;
            currentX = 0;
        }, { passive: true });

        // Touch cancel
        cardElement.addEventListener('touchcancel', () => {
            if (!isSwiping) return;

            cardElement.classList.remove('swiping', 'swipe-left');
            cardElement.style.transform = '';
            isSwiping = false;
            startX = 0;
            currentX = 0;
        }, { passive: true });
    }

    /**
     * Fade in element
     */
    function fadeIn(element, duration = 300) {
        return new Promise((resolve) => {
            element.style.opacity = '0';
            element.style.transition = `opacity ${duration}ms ease-in-out`;

            setTimeout(() => {
                element.style.opacity = '1';
            }, 10);

            setTimeout(() => {
                element.style.transition = '';
                resolve();
            }, duration);
        });
    }

    /**
     * Fade out element
     */
    function fadeOut(element, duration = 300) {
        return new Promise((resolve) => {
            element.style.transition = `opacity ${duration}ms ease-in-out`;
            element.style.opacity = '0';

            setTimeout(() => {
                element.style.transition = '';
                resolve();
            }, duration);
        });
    }

    /**
     * Slide down element (expand)
     */
    function slideDown(element, duration = 300) {
        return new Promise((resolve) => {
            element.style.height = '0';
            element.style.overflow = 'hidden';
            element.style.transition = `height ${duration}ms ease-in-out`;

            const height = element.scrollHeight;

            setTimeout(() => {
                element.style.height = `${height}px`;
            }, 10);

            setTimeout(() => {
                element.style.height = '';
                element.style.overflow = '';
                element.style.transition = '';
                resolve();
            }, duration);
        });
    }

    /**
     * Slide up element (collapse)
     */
    function slideUp(element, duration = 300) {
        return new Promise((resolve) => {
            const height = element.scrollHeight;
            element.style.height = `${height}px`;
            element.style.overflow = 'hidden';
            element.style.transition = `height ${duration}ms ease-in-out`;

            setTimeout(() => {
                element.style.height = '0';
            }, 10);

            setTimeout(() => {
                element.style.height = '';
                element.style.overflow = '';
                element.style.transition = '';
                resolve();
            }, duration);
        });
    }

    /**
     * Pulse animation for element (attention grabber)
     */
    function pulse(element, iterations = 1) {
        return new Promise((resolve) => {
            element.style.animation = `pulse 0.5s ease-in-out ${iterations}`;

            setTimeout(() => {
                element.style.animation = '';
                resolve();
            }, 500 * iterations);
        });
    }

    /**
     * Shake animation for element (error indication)
     */
    function shake(element) {
        return new Promise((resolve) => {
            element.style.animation = 'shake 0.5s ease-in-out';

            setTimeout(() => {
                element.style.animation = '';
                resolve();
            }, 500);
        });
    }

    /**
     * Show loading spinner
     */
    function showLoading(container) {
        const loader = document.createElement('div');
        loader.className = 'loading';
        loader.innerHTML = '<div class="spinner"></div>';
        container.appendChild(loader);
        return loader;
    }

    /**
     * Hide loading spinner
     */
    function hideLoading(loader) {
        if (loader && loader.parentNode) {
            loader.parentNode.removeChild(loader);
        }
    }

    // Add CSS for pulse and shake animations if not already present
    function injectAnimationStyles() {
        const styleId = 'animations-styles';
        if (document.getElementById(styleId)) return;

        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }

            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-10px); }
                75% { transform: translateX(10px); }
            }
        `;
        document.head.appendChild(style);
    }

    // Inject styles on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectAnimationStyles);
    } else {
        injectAnimationStyles();
    }

    // Public API
    return {
        animateCompletion,
        setupSwipeToDelete,
        fadeIn,
        fadeOut,
        slideDown,
        slideUp,
        pulse,
        shake,
        showLoading,
        hideLoading
    };
})();

// Make available globally
window.Animations = Animations;
