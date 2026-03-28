/* =====================================================
   GRAM-DRISHTI - JavaScript Application
   ===================================================== */

// Language Translations
const translations = {
  en: {
    "hero.title1": "Simple governance for ",
    "hero.title2": "every citizen.",
    "hero.subtitle":
      "Access village services, track budgets, and report issues directly from your phone or computer.",
    "action.login": "Aadhaar Login",
    "action.loginDesc": "Secure access to your personal dashboard",
    "action.budget": "Check Budget",
    "action.report": "Report Issue",
    "services.title": "Our Services",
    "services.certificates": "Certificates",
    "services.certificatesDesc": "Apply for Birth, Death, and Income papers.",
    "services.benefits": "Direct Benefits",
    "services.benefitsDesc": "Check PM-Kisan and subsidy statuses.",
    "services.education": "Education",
    "services.educationDesc": "School information and student training.",
    "services.health": "Health",
    "services.healthDesc": "Nearest health center and vaccine info.",
    help: "Help",
    "fund.title": "Current Fund Usage",
    "fund.subtitle": "Village Fund Utilization",
    "fund.verified": "Total Verified Funds",
    "fund.road": "Road Construction",
    "fund.water": "Clean Water",
    "fund.recentWins": "Recent Village Wins",
    "helpline.text": "Need help? Call the toll-free helpline:",
    "portals.title": "Access Portals",
    "portal.villager": "Villager Portal",
    "portal.villagerDesc": "Track issues, vote, view budget",
    "portal.sarpanch": "Sarpanch Portal",
    "portal.sarpanchDesc": "Manage complaints, assign work",
    "portal.admin": "Admin Panel",
    "portal.adminDesc": "System management, oversight",
    "portal.csc": "CSC Portal",
    "portal.cscDesc": "Quick actions for operators",
  },
  hi: {
    "hero.title1": "हर नागरिक के लिए ",
    "hero.title2": "सरल शासन।",
    "hero.subtitle":
      "ग्राम सेवाओं तक पहुंचें, बजट ट्रैक करें और सीधे अपने फ़ोन से समस्याओं की रिपोर्ट करें।",
    "action.login": "आधार लॉगिन",
    "action.loginDesc": "अपने व्यक्तिगत डैशबोर्ड तक सुरक्षित पहुंच",
    "action.budget": "बजट देखें",
    "action.report": "शिकायत दर्ज करें",
    "services.title": "हमारी सेवाएं",
    "services.certificates": "प्रमाण पत्र",
    "services.certificatesDesc":
      "जन्म, मृत्यु और आय प्रमाण पत्र के लिए आवेदन करें।",
    "services.benefits": "प्रत्यक्ष लाभ",
    "services.benefitsDesc": "पीएम-किसान और सब्सिडी की स्थिति जांचें।",
    "services.education": "शिक्षा",
    "services.educationDesc": "स्कूल की जानकारी और छात्र प्रशिक्षण।",
    "services.health": "स्वास्थ्य",
    "services.healthDesc": "निकटतम स्वास्थ्य केंद्र और टीके की जानकारी।",
    help: "सहायता",
    "fund.title": "वर्तमान निधि उपयोग",
    "fund.subtitle": "ग्राम निधि का उपयोग",
    "fund.verified": "कुल सत्यापित निधि",
    "fund.road": "सड़क निर्माण",
    "fund.water": "स्वच्छ जल",
    "fund.recentWins": "हाल की गाँव की उपलब्धियाँ",
    "helpline.text": "मदद चाहिए? टोल-फ्री हेल्पलाइन पर कॉल करें:",
    "portals.title": "पोर्टल एक्सेस करें",
    "portal.villager": "ग्रामीण पोर्टल",
    "portal.villagerDesc": "मुद्दों को ट्रैक करें, वोट करें, बजट देखें",
    "portal.sarpanch": "सरपंच पोर्टल",
    "portal.sarpanchDesc": "शिकायतों का प्रबंधन करें, काम सौंपें",
    "portal.admin": "व्यवस्थापक पैनल",
    "portal.adminDesc": "सिस्टम प्रबंधन, निरीक्षण",
    "portal.csc": "CSC पोर्टल",
    "portal.cscDesc": "ऑपरेटरों के लिए त्वरित कार्रवाई",
  },
};

// Current language state
let currentLang = "en";

// Initialize Application
document.addEventListener("DOMContentLoaded", function () {
  initLanguageToggle();
  initAnimations();
  initProgressBars();
  initFormValidation();
});

// Language Toggle Functionality
function initLanguageToggle() {
  const langButtons = document.querySelectorAll(".lang-btn");

  langButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
      const lang = this.dataset.lang;
      setLanguage(lang);

      // Update active state
      langButtons.forEach((b) => b.classList.remove("active"));
      this.classList.add("active");
    });
  });
}

function setLanguage(lang) {
  currentLang = lang;
  const elements = document.querySelectorAll("[data-i18n]");

  elements.forEach((el) => {
    const key = el.dataset.i18n;
    if (translations[lang] && translations[lang][key]) {
      el.textContent = translations[lang][key];
    }
  });

  // Update HTML lang attribute
  document.documentElement.lang = lang === "hi" ? "hi" : "en";
}

// Scroll Animations
function initAnimations() {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px",
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("animate-in");
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Observe elements for animation
  const animateElements = document.querySelectorAll(
    ".service-card, .portal-card, .win-item",
  );
  animateElements.forEach((el) => {
    el.style.opacity = "0";
    el.style.transform = "translateY(20px)";
    observer.observe(el);
  });
}

// Progress Bar Animation
function initProgressBars() {
  const progressBars = document.querySelectorAll(".progress-fill");

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const bar = entry.target;
          const width = bar.style.width;
          bar.style.width = "0%";
          setTimeout(() => {
            bar.style.width = width;
          }, 100);
          observer.unobserve(bar);
        }
      });
    },
    { threshold: 0.5 },
  );

  progressBars.forEach((bar) => observer.observe(bar));
}

// Form Validation
function initFormValidation() {
  const forms = document.querySelectorAll("form");

  forms.forEach((form) => {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      validateForm(this);
    });
  });
}

function validateForm(form) {
  const inputs = form.querySelectorAll("input[required], textarea[required]");
  let isValid = true;

  inputs.forEach((input) => {
    if (!input.value.trim()) {
      isValid = false;
      showError(input, "This field is required");
    } else {
      clearError(input);
    }
  });

  if (isValid) {
    // Submit form logic here
    showNotification("Form submitted successfully!", "success");
  }

  return isValid;
}

function showError(input, message) {
  const parent = input.parentElement;
  let errorEl = parent.querySelector(".error-message");

  if (!errorEl) {
    errorEl = document.createElement("span");
    errorEl.className = "error-message";
    parent.appendChild(errorEl);
  }

  errorEl.textContent = message;
  input.classList.add("error");
}

function clearError(input) {
  const parent = input.parentElement;
  const errorEl = parent.querySelector(".error-message");

  if (errorEl) {
    errorEl.remove();
  }
  input.classList.remove("error");
}

// Notification System
function showNotification(message, type = "info") {
  const notification = document.createElement("div");
  notification.className = `notification notification-${type}`;
  notification.innerHTML = `
        <span class="material-symbols-outlined">${getNotificationIcon(type)}</span>
        <span>${message}</span>
    `;

  document.body.appendChild(notification);

  // Animate in
  setTimeout(() => notification.classList.add("show"), 10);

  // Remove after 3 seconds
  setTimeout(() => {
    notification.classList.remove("show");
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

function getNotificationIcon(type) {
  const icons = {
    success: "check_circle",
    error: "error",
    warning: "warning",
    info: "info",
  };
  return icons[type] || icons.info;
}

// Modal System
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add("active");
    document.body.style.overflow = "hidden";
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove("active");
    document.body.style.overflow = "";
  }
}

// Close modal on backdrop click
document.addEventListener("click", function (e) {
  if (e.target.classList.contains("modal")) {
    e.target.classList.remove("active");
    document.body.style.overflow = "";
  }
});

// Voting System
function handleVote(issueId, vote) {
  console.log(`Vote ${vote} for issue ${issueId}`);
  showNotification(
    vote === "yes"
      ? "Vote recorded! Thank you for participating."
      : "Vote recorded.",
    "success",
  );
}

// Tab Navigation
function initTabs() {
  const tabButtons = document.querySelectorAll("[data-tab]");

  tabButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
      const tabId = this.dataset.tab;
      const tabContent = document.getElementById(tabId);

      // Hide all tabs
      document.querySelectorAll(".tab-content").forEach((tab) => {
        tab.classList.remove("active");
      });

      // Remove active from all buttons
      tabButtons.forEach((b) => b.classList.remove("active"));

      // Show selected tab
      if (tabContent) {
        tabContent.classList.add("active");
      }
      this.classList.add("active");
    });
  });
}

// Sidebar Toggle (for dashboard pages)
function toggleSidebar() {
  const sidebar = document.querySelector(".sidebar");
  if (sidebar) {
    sidebar.classList.toggle("collapsed");
  }
}

// Search Functionality
function initSearch() {
  const searchInputs = document.querySelectorAll(".search-input");

  searchInputs.forEach((input) => {
    input.addEventListener(
      "input",
      debounce(function () {
        const query = this.value.toLowerCase();
        const searchableItems = document.querySelectorAll("[data-searchable]");

        searchableItems.forEach((item) => {
          const text = item.textContent.toLowerCase();
          item.style.display = text.includes(query) ? "" : "none";
        });
      }, 300),
    );
  });
}

// Debounce utility
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func.apply(this, args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Format Currency
function formatCurrency(amount) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

// Format Date
function formatDate(dateString) {
  const options = { year: "numeric", month: "long", day: "numeric" };
  return new Date(dateString).toLocaleDateString("en-IN", options);
}

// Add CSS for animations dynamically
const animationStyles = document.createElement("style");
animationStyles.textContent = `
    .animate-in {
        opacity: 1 !important;
        transform: translateY(0) !important;
        transition: all 0.6s ease-out;
    }
    
    .notification {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        padding: 1rem 1.5rem;
        background: #1e293b;
        color: white;
        border-radius: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        transform: translateY(100px);
        opacity: 0;
        transition: all 0.3s ease;
        z-index: 9999;
    }
    
    .notification.show {
        transform: translateY(0);
        opacity: 1;
    }
    
    .notification-success {
        background: #059669;
    }
    
    .notification-error {
        background: #dc2626;
    }
    
    .notification-warning {
        background: #d97706;
    }
    
    .error-message {
        display: block;
        color: #dc2626;
        font-size: 0.75rem;
        margin-top: 0.25rem;
    }
    
    input.error, textarea.error {
        border-color: #dc2626 !important;
    }
    
    .modal {
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
        z-index: 1000;
    }
    
    .modal.active {
        opacity: 1;
        visibility: visible;
    }
    
    .modal-content {
        background: white;
        border-radius: 1.5rem;
        padding: 2rem;
        max-width: 500px;
        width: 90%;
        transform: scale(0.9);
        transition: transform 0.3s ease;
    }
    
    .modal.active .modal-content {
        transform: scale(1);
    }
`;
document.head.appendChild(animationStyles);

// ── Security Utility ──────────────────────────────────────────
// Escapes user-controlled strings before inserting into innerHTML
// to prevent XSS attacks.
window.escapeHtml = function (str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
};

// ── Dynamic Copyright Year ─────────────────────────────────────
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".copyright-year").forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });
});
