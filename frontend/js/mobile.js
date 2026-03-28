/* ══════════════════════════════════════════════════════════════
   GRAM-DRISHTI  –  Premium Mobile Responsiveness JS
   ══════════════════════════════════════════════════════════════
   Auto-injects: hamburger menu, sidebar overlay with swipe,
   bottom navigation bar, ripple tap effects, and smooth
   scroll behavior — all for phone-first UX.
   ══════════════════════════════════════════════════════════════ */
(function() {
    'use strict';

    var MOBILE_BP = 768;

    function isMobile() {
        return window.innerWidth <= MOBILE_BP;
    }

    document.addEventListener('DOMContentLoaded', function() {
        var sidebar = document.querySelector('.sidebar');
        var header  = document.querySelector('.admin-header');
        var hamburger = null;
        var overlay = null;

        /* ── Hamburger Button ── */
        if (header) {
            hamburger = document.createElement('button');
            hamburger.className = 'hamburger-btn';
            hamburger.setAttribute('aria-label', 'Open navigation menu');
            hamburger.innerHTML = '<span class="material-symbols-outlined">menu</span>';
            header.insertBefore(hamburger, header.firstChild);
        }

        /* ── Sidebar Overlay ── */
        if (sidebar) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-mobile-overlay';
            overlay.setAttribute('aria-hidden', 'true');
            document.body.appendChild(overlay);

            function openSidebar() {
                sidebar.classList.add('mobile-open');
                overlay.classList.add('show');
                document.body.style.overflow = 'hidden';
                if (hamburger) {
                    hamburger.innerHTML = '<span class="material-symbols-outlined">close</span>';
                    hamburger.setAttribute('aria-label', 'Close navigation menu');
                }
                /* Focus first nav item for accessibility */
                var firstNav = sidebar.querySelector('.nav-item');
                if (firstNav) setTimeout(function() { firstNav.focus(); }, 100);
            }

            function closeSidebar() {
                sidebar.classList.remove('mobile-open');
                overlay.classList.remove('show');
                document.body.style.overflow = '';
                if (hamburger) {
                    hamburger.innerHTML = '<span class="material-symbols-outlined">menu</span>';
                    hamburger.setAttribute('aria-label', 'Open navigation menu');
                }
            }

            if (hamburger) {
                hamburger.addEventListener('click', function(e) {
                    e.stopPropagation();
                    if (sidebar.classList.contains('mobile-open')) {
                        closeSidebar();
                    } else {
                        openSidebar();
                    }
                });
            }

            overlay.addEventListener('click', closeSidebar);

            /* Swipe-to-close on sidebar (swipe left) */
            var touchStartX = 0;
            var touchStartY = 0;
            sidebar.addEventListener('touchstart', function(e) {
                touchStartX = e.touches[0].clientX;
                touchStartY = e.touches[0].clientY;
            }, { passive: true });
            sidebar.addEventListener('touchend', function(e) {
                var deltaX = e.changedTouches[0].clientX - touchStartX;
                var deltaY = Math.abs(e.changedTouches[0].clientY - touchStartY);
                if (deltaX < -50 && deltaY < 80) closeSidebar(); /* left swipe */
            }, { passive: true });

            /* Swipe-to-open from left edge of screen */
            var edgeTouchX = 0;
            document.addEventListener('touchstart', function(e) {
                if (e.touches[0].clientX < 20) { /* Near left edge */
                    edgeTouchX = e.touches[0].clientX;
                }
            }, { passive: true });
            document.addEventListener('touchend', function(e) {
                if (edgeTouchX > 0) {
                    var deltaX = e.changedTouches[0].clientX - edgeTouchX;
                    if (deltaX > 60 && isMobile() && !sidebar.classList.contains('mobile-open')) {
                        openSidebar();
                    }
                    edgeTouchX = 0;
                }
            }, { passive: true });

            /* Close sidebar on nav link click (mobile) */
            sidebar.querySelectorAll('.nav-item').forEach(function(item) {
                item.addEventListener('click', function() {
                    if (isMobile()) {
                        setTimeout(closeSidebar, 150);
                    }
                });
            });

            /* Escape key closes sidebar */
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && sidebar.classList.contains('mobile-open')) {
                    closeSidebar();
                    if (hamburger) hamburger.focus();
                }
            });
        }

        /* ── Bottom Navigation Bar ── */
        injectBottomNav();

        /* ── Ripple Effect on interactive elements ── */
        if (isMobile()) initRippleEffect();

        /* ── Resize handler ── */
        var resizeTimer;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function() {
                if (!isMobile() && sidebar) {
                    sidebar.classList.remove('mobile-open');
                    if (overlay) overlay.classList.remove('show');
                    document.body.style.overflow = '';
                    if (hamburger) {
                        hamburger.innerHTML = '<span class="material-symbols-outlined">menu</span>';
                    }
                }
            }, 200);
        });

        /* ── Hide bottom nav on scroll down, show on scroll up ── */
        if (isMobile()) initScrollHideNav();
    });

    /* ═════════════════════════════════════════════
       Bottom Nav — Context-aware per portal
    ═════════════════════════════════════════════ */
    function injectBottomNav() {
        var path = window.location.pathname.split('/').pop() || '';
        var pageName = path.toLowerCase().replace('.html', '');

        var sarpanchNav = [
            { icon:'dashboard',              label:'Home',        href:'sarpanch-portal.html',   page:'sarpanch-portal' },
            { icon:'campaign',               label:'Issues',      href:'community-issues.html',  page:'community-issues' },
            { icon:'construction',           label:'Projects',    href:'active-projects.html',   page:'active-projects' },
            { icon:'groups',                 label:'Contractors', href:'contractors.html',        page:'contractors' },
            { icon:'account_balance_wallet', label:'Budget',      href:'public-ledger.html',     page:'public-ledger' },
        ];
        var villagerNav = [
            { icon:'dashboard',              label:'Home',    href:'villager-dashboard.html', page:'villager-dashboard' },
            { icon:'report_problem',         label:'Report',  href:'raise-issue.html',        page:'raise-issue' },
            { icon:'account_balance_wallet', label:'Budget',  href:'public-ledger.html',      page:'public-ledger' },
            { icon:'person',                 label:'Profile', href:'my-profile.html',          page:'my-profile' },
        ];
        var adminNav = [
            { icon:'dashboard',        label:'Dashboard', href:'admin-panel.html',     page:'admin-panel' },
            { icon:'people',           label:'Users',     href:'user-management.html', page:'user-management' },
            { icon:'location_city',    label:'Villages',  href:'village-registry.html', page:'village-registry' },
            { icon:'settings',         label:'Settings',  href:'system-settings.html', page:'system-settings' },
        ];

        var navItems = null;
        var sarpanchPages = ['sarpanch-portal','community-issues','active-projects','contractors','pending-approvals','contractor-verification','public-ledger'];
        var villagerPages = ['villager-dashboard','raise-issue','my-profile'];
        var adminPages = ['admin-panel','user-management','village-registry','system-settings','security-audit'];

        if (sarpanchPages.indexOf(pageName) >= 0) navItems = sarpanchNav;
        else if (villagerPages.indexOf(pageName) >= 0) navItems = villagerNav;
        else if (adminPages.indexOf(pageName) >= 0) navItems = adminNav;

        if (!navItems) return;

        var nav = document.createElement('nav');
        nav.className = 'mobile-bottom-nav';
        nav.setAttribute('aria-label', 'Quick navigation');

        var inner = document.createElement('div');
        inner.className = 'mobile-bottom-nav-inner';

        navItems.forEach(function(item) {
            var a = document.createElement('a');
            a.href = item.href;
            a.className = 'mob-nav-item' + (pageName === item.page ? ' active' : '');
            a.setAttribute('aria-label', item.label);
            a.innerHTML =
                '<span class="material-symbols-outlined" aria-hidden="true">' + item.icon + '</span>' +
                '<span>' + item.label + '</span>';

            /* Haptic-like visual feedback on tap */
            a.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.82)';
            }, { passive: true });
            a.addEventListener('touchend', function() {
                var el = this;
                el.style.transform = '';
                /* Brief pulse on active */
                if (!el.classList.contains('active')) {
                    el.style.background = '#f0fdf4';
                    setTimeout(function() { el.style.background = ''; }, 200);
                }
            }, { passive: true });

            inner.appendChild(a);
        });

        nav.appendChild(inner);
        document.body.appendChild(nav);
    }

    /* ═════════════════════════════════════════════
       Ripple Tap Effect — Material-style
    ═════════════════════════════════════════════ */
    function initRippleEffect() {
        var selectors = [
            '.action-card', '.portal-card', '.service-card',
            '.nav-item', '.hamburger-btn',
            '.assign-issue-btn', '.modal-confirm-btn',
            '.contractor-pick-item', '.focus-card',
            '.stat-card', '.issue-card'
        ];

        document.addEventListener('click', function(e) {
            var target = e.target.closest(selectors.join(','));
            if (!target || !isMobile()) return;

            /* Create ripple circle */
            var circle = document.createElement('span');
            circle.className = 'ripple-circle';
            var rect = target.getBoundingClientRect();
            var size = Math.max(rect.width, rect.height);
            circle.style.width = circle.style.height = size + 'px';
            circle.style.left = (e.clientX - rect.left - size / 2) + 'px';
            circle.style.top  = (e.clientY - rect.top  - size / 2) + 'px';

            /* Ensure parent has overflow hidden and relative position */
            target.style.position = target.style.position || 'relative';
            target.style.overflow = 'hidden';
            target.appendChild(circle);

            /* Remove after animation */
            setTimeout(function() { circle.remove(); }, 500);
        });
    }

    /* ═════════════════════════════════════════════
       Hide Bottom Nav on Scroll Down
    ═════════════════════════════════════════════ */
    function initScrollHideNav() {
        var lastScroll = 0;
        var bottomNav = null;
        var threshold = 10;

        /* Wait a bit for the nav to be injected */
        setTimeout(function() {
            bottomNav = document.querySelector('.mobile-bottom-nav');
            if (!bottomNav) return;

            var scrollHandler = function() {
                var current = window.pageYOffset || document.documentElement.scrollTop;
                if (current <= 0) {
                    bottomNav.style.transform = '';
                    lastScroll = current;
                    return;
                }
                if (current > lastScroll + threshold) {
                    /* Scrolling down — hide */
                    bottomNav.style.transform = 'translateY(100%)';
                    bottomNav.style.transition = 'transform 0.28s cubic-bezier(0.4, 0, 0.2, 1)';
                } else if (current < lastScroll - threshold) {
                    /* Scrolling up — show */
                    bottomNav.style.transform = 'translateY(0)';
                    bottomNav.style.transition = 'transform 0.28s cubic-bezier(0.4, 0, 0.2, 1)';
                }
                lastScroll = current;
            };

            /* Throttle scroll events */
            var ticking = false;
            window.addEventListener('scroll', function() {
                if (!ticking) {
                    window.requestAnimationFrame(function() {
                        scrollHandler();
                        ticking = false;
                    });
                    ticking = true;
                }
            }, { passive: true });
        }, 500);
    }
})();
