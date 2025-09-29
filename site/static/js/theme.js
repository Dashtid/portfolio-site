/**
 * Modern Theme Manager with ES6+ features
 * Handles dark/light theme switching and back-to-top functionality
 */

class ThemeManager {
  constructor() {
    this.storageKey = 'theme'
    this.modeKey = 'theme-mode' // 'system' or 'manual'
    this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    this.currentMode = this.getInitialMode()
    this.currentTheme = this.getInitialTheme()

    this.init()
  }

  getInitialMode() {
    return localStorage.getItem(this.modeKey) || 'system'
  }

  getInitialTheme() {
    const mode = this.getInitialMode()
    if (mode === 'system') {
      return this.mediaQuery.matches ? 'dark' : 'light'
    }
    const saved = localStorage.getItem(this.storageKey)
    return saved || (this.mediaQuery.matches ? 'dark' : 'light')
  }

  setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme)
    if (this.currentMode === 'manual') {
      localStorage.setItem(this.storageKey, theme)
    }
    this.currentTheme = theme

    // Dispatch custom event for other components
    window.dispatchEvent(
      new CustomEvent('themeChanged', {
        detail: { theme, mode: this.currentMode, isDark: theme === 'dark' }
      })
    )
  }

  setMode(mode) {
    this.currentMode = mode
    localStorage.setItem(this.modeKey, mode)

    if (mode === 'system') {
      // Clear manual theme preference and use system
      localStorage.removeItem(this.storageKey)
      this.setTheme(this.mediaQuery.matches ? 'dark' : 'light')
    } else {
      // Switch to manual mode and keep current theme
      this.setTheme(this.currentTheme)
    }
  }

  updateSlider(slider) {
    const isManualMode = this.currentMode === 'manual'
    slider.setAttribute('aria-checked', isManualMode ? 'true' : 'false')
    slider.setAttribute(
      'aria-label',
      `Theme mode: ${this.currentMode}. Click to switch to ${isManualMode ? 'system' : 'manual'} mode`
    )
  }

  updateLightDarkToggle(toggle) {
    const isDark = this.currentTheme === 'dark'
    toggle.setAttribute('aria-checked', isDark ? 'true' : 'false')
    toggle.setAttribute(
      'aria-label',
      `Current theme: ${this.currentTheme}. Click to switch to ${isDark ? 'light' : 'dark'} theme`
    )
  }

  showManualToggle() {
    const manualToggle = document.getElementById('manualThemeToggle')
    if (manualToggle) {
      manualToggle.classList.remove('hidden')
      setTimeout(() => {
        manualToggle.classList.add('show')
      }, 10)
    }
  }

  hideManualToggle() {
    const manualToggle = document.getElementById('manualThemeToggle')
    if (manualToggle) {
      manualToggle.classList.remove('show')
      setTimeout(() => {
        manualToggle.classList.add('hidden')
      }, 300)
    }
  }

  toggleMode() {
    const nextMode = this.currentMode === 'system' ? 'manual' : 'system'
    this.setMode(nextMode)
    return nextMode
  }

  toggleTheme() {
    const nextTheme = this.currentTheme === 'dark' ? 'light' : 'dark'
    this.setTheme(nextTheme)
    return nextTheme
  }

  init() {
    // Set initial theme
    this.setTheme(this.currentTheme)

    // Setup theme toggle slider
    const themeSlider = document.getElementById('themeToggle')
    const lightDarkToggle = document.getElementById('lightDarkToggle')

    if (themeSlider) {
      this.updateSlider(themeSlider)

      // Handle mode switching (system/manual)
      themeSlider.addEventListener('click', () => {
        const newMode = this.toggleMode()
        this.updateSlider(themeSlider)

        if (newMode === 'manual') {
          this.showManualToggle()
          if (lightDarkToggle) {
            this.updateLightDarkToggle(lightDarkToggle)
          }
        } else {
          this.hideManualToggle()
        }
      })

      // Handle keyboard events for accessibility
      themeSlider.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          const newMode = this.toggleMode()
          this.updateSlider(themeSlider)

          if (newMode === 'manual') {
            this.showManualToggle()
            if (lightDarkToggle) {
              this.updateLightDarkToggle(lightDarkToggle)
            }
          } else {
            this.hideManualToggle()
          }
        }
      })

      // Mobile Safari focus fix
      if (this.isMobileSafari()) {
        themeSlider.addEventListener('touchstart', () => {
          themeSlider.focus()
        })
      }
    }

    // Setup light/dark theme toggle (only visible in manual mode)
    if (lightDarkToggle) {
      this.updateLightDarkToggle(lightDarkToggle)

      // Handle theme switching (light/dark)
      lightDarkToggle.addEventListener('click', () => {
        if (this.currentMode === 'manual') {
          this.toggleTheme()
          this.updateLightDarkToggle(lightDarkToggle)
        }
      })

      // Handle keyboard events for accessibility
      lightDarkToggle.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          if (this.currentMode === 'manual') {
            this.toggleTheme()
            this.updateLightDarkToggle(lightDarkToggle)
          }
        }
      })

      // Mobile Safari focus fix for light/dark toggle
      if (this.isMobileSafari()) {
        lightDarkToggle.addEventListener('touchstart', () => {
          lightDarkToggle.focus()
        })
      }
    }

    // Show/hide manual toggle based on initial mode
    if (this.currentMode === 'manual') {
      this.showManualToggle()
    } else {
      this.hideManualToggle()
    }

    // Listen for system theme changes
    this.mediaQuery.addEventListener('change', e => {
      if (this.currentMode === 'system') {
        const systemTheme = e.matches ? 'dark' : 'light'
        this.setTheme(systemTheme)
      }
    })
  }

  /**
   * Detect Mobile Safari for specific fixes
   */
  isMobileSafari() {
    return (
      /iPad|iPhone|iPod/.test(navigator.userAgent) &&
      /Safari/.test(navigator.userAgent) &&
      !/Chrome/.test(navigator.userAgent)
    )
  }
}

class ScrollManager {
  constructor() {
    this.threshold = 300
    this.isVisible = false
    this.button = document.getElementById('backToTopBtn')
    this.navHeight = 80

    if (this.button) {
      this.init()
    }
    this.initSmoothScrolling()
  }

  toggleVisibility() {
    const shouldShow = window.pageYOffset > this.threshold

    if (shouldShow !== this.isVisible) {
      this.isVisible = shouldShow
      this.button.style.display = shouldShow ? 'block' : 'none'
      this.button.setAttribute('aria-hidden', !shouldShow)
    }
  }

  scrollToTop() {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    })

    // Focus management for accessibility
    setTimeout(() => {
      document.querySelector('h1, [tabindex="0"]')?.focus()
    }, 100)
  }

  init() {
    // Use passive listener for better performance
    window.addEventListener(
      'scroll',
      () => {
        requestAnimationFrame(() => {
          try {
            this.toggleVisibility()
          } catch (error) {
            // Gracefully handle scroll visibility errors
            // eslint-disable-next-line no-console
            console.warn('Error in scroll visibility toggle:', error)
          }
        })
      },
      { passive: true }
    )

    this.button.addEventListener('click', e => {
      e.preventDefault()
      this.scrollToTop()
    })

    // Initial check
    this.toggleVisibility()
  }

  initSmoothScrolling() {
    // Handle internal navigation links
    const internalNavLinks = document.querySelectorAll(
      '.internal-nav[data-scroll]'
    )

    internalNavLinks.forEach(link => {
      link.addEventListener('click', e => {
        e.preventDefault()
        const targetId = link.getAttribute('data-scroll')
        this.scrollToSection(targetId)

        // Update active state immediately for manual navigation
        this.updateActiveNavLink(link)

        // Force update after scrolling completes
        setTimeout(() => {
          this.updateActiveNavLink(link)
        }, 500)

        // Close mobile menu if open
        const navbar = document.querySelector('.navbar-collapse')
        if (navbar && navbar.classList.contains('show')) {
          navbar.classList.remove('show')
        }
      })
    })

    // Intersection Observer for active navigation highlighting
    this.setupNavigationHighlighting()
  }

  scrollToSection(targetId) {
    const target = document.getElementById(targetId)
    if (!target) return

    try {
      const targetPosition =
        target.getBoundingClientRect().top + window.pageYOffset - this.navHeight

      window.scrollTo({
        top: targetPosition,
        behavior: 'smooth'
      })
    } catch (error) {
      // Gracefully handle getBoundingClientRect errors
      // eslint-disable-next-line no-console
      console.warn('Error getting target position for scroll:', error)
      // Fallback: scroll to top of element without precise positioning
      if (typeof target.scrollIntoView === 'function') {
        try {
          target.scrollIntoView({ behavior: 'smooth' })
        } catch (fallbackError) {
          // eslint-disable-next-line no-console
          console.warn('Error with scrollIntoView fallback:', fallbackError)
        }
      }
    }

    // Update URL without triggering page reload
    try {
      history.pushState(null, null, `#${targetId}`)
    } catch (error) {
      // eslint-disable-next-line no-console
      console.warn('Error updating URL hash:', error)
    }
  }

  updateActiveNavLink(activeLink) {
    // Remove active class from all internal nav links
    document.querySelectorAll('.internal-nav').forEach(link => {
      link.classList.remove('active')
      link.removeAttribute('aria-current')
    })

    // Add active class to current link
    activeLink.classList.add('active')
    activeLink.setAttribute('aria-current', 'page')
  }

  setupNavigationHighlighting() {
    const sections = document.querySelectorAll('section[id]')
    let currentActiveSection = null

    const observer = new IntersectionObserver(
      entries => {
        // Sort entries by intersection ratio and position
        const visibleEntries = entries
          .filter(entry => entry.isIntersecting)
          .sort((a, b) => {
            // First by intersection ratio (higher is better)
            const ratioDiff = b.intersectionRatio - a.intersectionRatio
            if (Math.abs(ratioDiff) > 0.1) return ratioDiff

            // Then by vertical position (higher on screen is better)
            return a.boundingClientRect.top - b.boundingClientRect.top
          })

        if (visibleEntries.length > 0) {
          const topSection = visibleEntries[0].target

          // Only update if this is a different section and target exists
          if (topSection && currentActiveSection !== topSection.id) {
            currentActiveSection = topSection.id
            const currentNavLink = document.querySelector(
              `[data-scroll="${topSection.id}"]`
            )
            if (currentNavLink) {
              this.updateActiveNavLink(currentNavLink)
            }
          }
        }
      },
      {
        threshold: [0, 0.1, 0.25, 0.5, 0.75, 1],
        rootMargin: `-${this.navHeight}px 0px -30% 0px`
      }
    )

    sections.forEach(section => observer.observe(section))
  }
}

class ProjectManager {
  constructor() {
    this.projects = []
    this.currentFilter = 'all'
    this.currentSort = 'updated'
    this.categories = {
      cybersecurity: [
        'security',
        'cyber',
        'auth',
        'encryption',
        'vulnerability',
        'pentest'
      ],
      healthcare: ['medical', 'health', 'hospital', 'patient', 'dicom', 'pacs'],
      automation: [
        'script',
        'automation',
        'deploy',
        'ci',
        'cd',
        'pipeline',
        'workflow'
      ],
      tools: ['tool', 'utility', 'helper', 'cli', 'api', 'framework']
    }

    this.init()
  }

  init() {
    this.setupEventListeners()
    // this.interceptRepoWidget() // Disabled to prevent conflicts with direct widget initialization
  }

  setupEventListeners() {
    // Filter buttons
    const filterButtons = document.querySelectorAll('.filter-btn')
    filterButtons.forEach(btn => {
      btn.addEventListener('click', e => {
        this.setFilter(e.target.getAttribute('data-filter'))
        this.updateFilterButtons(e.target)
      })
    })

    // Sort dropdown
    const sortSelect = document.getElementById('repo-sort')
    if (sortSelect) {
      sortSelect.addEventListener('change', e => {
        this.currentSort = e.target.value
        this.applyFiltersAndSort()
      })
    }
  }

  setFilter(filter) {
    this.currentFilter = filter
    this.applyFiltersAndSort()
  }

  updateFilterButtons(activeButton) {
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.classList.remove('active')
      btn.setAttribute('aria-pressed', 'false')
    })

    activeButton.classList.add('active')
    activeButton.setAttribute('aria-pressed', 'true')
  }

  categorizeProject(project) {
    const text = `${project.name} ${project.description || ''}`.toLowerCase()

    for (const [category, keywords] of Object.entries(this.categories)) {
      if (keywords.some(keyword => text.includes(keyword))) {
        return category
      }
    }
    return 'other'
  }

  filterProjects() {
    if (this.currentFilter === 'all') {
      return this.projects
    }

    return this.projects.filter(project => {
      const category = this.categorizeProject(project)
      return category === this.currentFilter
    })
  }

  sortProjects(projects) {
    return [...projects].sort((a, b) => {
      switch (this.currentSort) {
        case 'name':
          return a.name.localeCompare(b.name)
        case 'stars':
          return (b.stargazers_count || 0) - (a.stargazers_count || 0)
        case 'created':
          return new Date(b.created_at) - new Date(a.created_at)
        case 'updated':
        default:
          return new Date(b.updated_at) - new Date(a.updated_at)
      }
    })
  }

  applyFiltersAndSort() {
    const filtered = this.filterProjects()
    const sorted = this.sortProjects(filtered)
    this.renderProjects(sorted)
  }

  renderProjects(projects) {
    const container = document.getElementById('repo-container')
    const noResults = document.getElementById('no-results')

    if (projects.length === 0) {
      container.style.display = 'none'
      noResults.style.display = 'block'
    } else {
      container.style.display = 'block'
      noResults.style.display = 'none'

      // Clear existing content and create row structure
      container.innerHTML = '<div class="row" id="projects-row"></div>'
      const projectsRow = container.querySelector('#projects-row')

      // Create project cards
      projects.forEach(project => {
        const card = this.createProjectCard(project)
        projectsRow.appendChild(card)
      })
    }
  }

  createProjectCard(project) {
    const card = document.createElement('div')
    card.className = 'col-md-6 col-lg-4 mb-4'

    const category = this.categorizeProject(project)
    const categoryBadge =
      category !== 'other'
        ? `<span class="badge bg-secondary mb-2">${category}</span>`
        : ''

    card.innerHTML = `
      <div class="card h-100 project-card" data-category="${category}">
        <div class="card-body d-flex flex-column">
          ${categoryBadge}
          <h5 class="card-title">${project.name}</h5>
          <p class="card-text flex-grow-1">${project.description || 'No description available'}</p>
          <div class="d-flex justify-content-between align-items-center mt-auto">
            <small class="text-muted">
              ${project.language ? `<span class="me-3">📝 ${project.language}</span>` : ''}
              ${project.stargazers_count ? `⭐ ${project.stargazers_count}` : ''}
            </small>
            <a href="${project.html_url}" target="_blank" rel="noopener" 
               class="btn btn-sm btn-outline-primary"
               aria-label="View ${project.name} on GitHub">
              View →
            </a>
          </div>
        </div>
      </div>
    `

    return card
  }

  interceptRepoWidget() {
    // Override the repoWidget to capture project data
    if (typeof window.createRepoWidget === 'undefined') {
      // If repoWidget isn't loaded yet, wait for it
      const checkForWidget = () => {
        if (typeof window.createRepoWidget === 'function') {
          this.setupWidgetOverride()
        } else {
          setTimeout(checkForWidget, 100)
        }
      }
      checkForWidget()
    } else {
      this.setupWidgetOverride()
    }
  }

  setupWidgetOverride() {
    const originalCreateRepoWidget = window.createRepoWidget

    window.createRepoWidget = config => {
      try {
        // Store the original config
        const originalCallback =
          config.onLoad ||
          function () {
            return undefined
          }

        // Override onLoad to capture data
        config.onLoad = projects => {
          this.projects = projects || []
          this.hideLoading()
          this.applyFiltersAndSort()
          originalCallback(projects)
        }

        // Call original function
        return originalCreateRepoWidget(config)
      } catch (error) {
        // Handle repo widget setup errors
        this.hideLoading()
        return null
      }
    }
  }

  hideLoading() {
    const loading = document.getElementById('repo-loading')
    if (loading) {
      loading.style.display = 'none'
    }
  }
}

class IconManager {
  constructor() {
    this.iconMappings = {
      // Define mappings from original icons to their white variants
      'static/images/D.svg': 'static/images/D-white.svg',
      'static/images/github.svg': 'static/images/github-white.svg',
      'static/images/experience.svg': 'static/images/experience-white.svg',
      'static/images/education.svg': 'static/images/education-white.svg',
      'static/images/about.svg': 'static/images/about-white.svg',
      'static/images/contact.svg': 'static/images/contact-white.svg',
      'static/images/LinkedIn.svg': 'static/images/LinkedIn-white.svg',
      '../static/images/D.svg': '../static/images/D-white.svg'
    }

    this.currentTheme = null
    this.managedIcons = new Map() // Cache for managed icon elements
    this.faviconElement = null

    this.init()
  }

  init() {
    // Find and cache all manageable icons
    this.discoverIcons()

    // Find favicon element
    this.faviconElement = document.querySelector('link[rel="icon"]')

    // Listen for theme changes
    window.addEventListener('themeChanged', event => {
      this.handleThemeChange(event.detail)
    })

    // Set initial state based on current theme
    const currentTheme =
      document.documentElement.getAttribute('data-theme') || 'light'
    this.handleThemeChange({
      theme: currentTheme,
      isDark: currentTheme === 'dark'
    })
  }

  discoverIcons() {
    // Find all img elements with section-icon or contact-icon classes
    const sectionIcons = document.querySelectorAll('.section-icon')
    const contactIcons = document.querySelectorAll('.contact-icon')
    const githubIcons = document.querySelectorAll('img[src*="github.svg"]')

    // Combine all icon sets
    const allIcons = [...sectionIcons, ...contactIcons, ...githubIcons]

    allIcons.forEach(icon => {
      const src = icon.getAttribute('src')
      if (src && this.iconMappings[src]) {
        // Store original src and element reference
        this.managedIcons.set(icon, {
          originalSrc: src,
          whiteSrc: this.iconMappings[src],
          element: icon
        })
      }
    })
  }

  handleThemeChange(themeData) {
    const { theme, isDark } = themeData

    if (this.currentTheme === theme) return // No change needed

    this.currentTheme = theme

    // Update favicon
    this.updateFavicon(isDark)

    // Update all managed icons
    this.updateIcons(isDark)

    // Remove CSS filters since we're now using proper icon variants
    this.removeCSSFilters()
  }

  updateFavicon(isDark) {
    if (!this.faviconElement) return

    const faviconSrc = isDark
      ? 'static/images/D-white.svg'
      : 'static/images/D.svg'

    // Only update if different
    if (this.faviconElement.getAttribute('href') !== faviconSrc) {
      this.faviconElement.setAttribute('href', faviconSrc)
    }
  }

  updateIcons(isDark) {
    this.managedIcons.forEach((iconData, element) => {
      const targetSrc = isDark ? iconData.whiteSrc : iconData.originalSrc

      // Only update if different (performance optimization)
      if (element.getAttribute('src') !== targetSrc) {
        element.setAttribute('src', targetSrc)

        // Update alt text for accessibility
        if (isDark && !element.getAttribute('alt').includes('(dark mode)')) {
          const currentAlt = element.getAttribute('alt') || ''
          element.setAttribute('alt', `${currentAlt} (dark mode variant)`)
        } else if (
          !isDark &&
          element.getAttribute('alt').includes('(dark mode)')
        ) {
          const currentAlt = element.getAttribute('alt') || ''
          element.setAttribute(
            'alt',
            currentAlt.replace(' (dark mode variant)', '')
          )
        }
      }
    })
  }

  removeCSSFilters() {
    // Remove the CSS filter rules that were used for dark mode icon conversion
    const { styleSheets } = document

    for (let i = 0; i < styleSheets.length; i++) {
      try {
        const rules = styleSheets[i].cssRules || styleSheets[i].rules
        if (!rules) continue

        for (let j = rules.length - 1; j >= 0; j--) {
          const rule = rules[j]
          if (
            rule.selectorText &&
            rule.selectorText.includes("[data-theme='dark']") &&
            rule.style &&
            rule.style.filter &&
            rule.style.filter.includes('invert')
          ) {
            styleSheets[i].deleteRule(j)
          }
        }
      } catch (e) {
        // Skip stylesheets we can't access (CORS)
        continue
      }
    }
  }

  // Method to add new icons dynamically (for future use)
  addIcon(element, originalSrc) {
    if (this.iconMappings[originalSrc]) {
      this.managedIcons.set(element, {
        originalSrc,
        whiteSrc: this.iconMappings[originalSrc],
        element
      })

      // Apply current theme immediately
      this.updateIcons(this.currentTheme === 'dark')
    }
  }

  // Performance method: preload all icon variants
  preloadIcons() {
    const iconSources = new Set()

    // Collect all unique icon sources
    Object.values(this.iconMappings).forEach(src => iconSources.add(src))
    Object.keys(this.iconMappings).forEach(src => iconSources.add(src))

    // Preload each icon
    iconSources.forEach(src => {
      const img = new Image()
      img.src = src
    })
  }
}

class AnimationManager {
  constructor() {
    this.animatedElements = new Set()
    this.init()
  }

  init() {
    this.setupScrollAnimations()
    this.animateProgressBars()
    this.setupCardAnimations()
  }

  setupScrollAnimations() {
    const sections = document.querySelectorAll('section')

    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('section-animate', 'visible')

            // Animate skills progress bars when skills section comes into view
            if (entry.target && entry.target.id === 'skills') {
              this.animateSkillsBars()
            }
          }
        })
      },
      {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
      }
    )

    sections.forEach(section => {
      section.classList.add('section-animate')
      observer.observe(section)
    })
  }

  animateSkillsBars() {
    const progressBars = document.querySelectorAll('#skills .progress-bar')

    progressBars.forEach((bar, index) => {
      const targetWidth = bar.style.width
      bar.style.width = '0%'

      setTimeout(() => {
        bar.style.width = targetWidth
      }, index * 100)
    })
  }

  animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar')

    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (
            entry.isIntersecting &&
            !this.animatedElements.has(entry.target)
          ) {
            const targetWidth = `${entry.target.getAttribute('aria-valuenow')}%`
            entry.target.style.width = '0%'

            setTimeout(() => {
              entry.target.style.width = targetWidth
            }, 200)

            this.animatedElements.add(entry.target)
          }
        })
      },
      { threshold: 0.5 }
    )

    progressBars.forEach(bar => observer.observe(bar))
  }

  setupCardAnimations() {
    const cards = document.querySelectorAll('.card')

    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (
            entry.isIntersecting &&
            !this.animatedElements.has(entry.target)
          ) {
            entry.target.classList.add('fade-in')
            this.animatedElements.add(entry.target)
          }
        })
      },
      { threshold: 0.1 }
    )

    cards.forEach(card => observer.observe(card))
  }

  // Add loading state management
  showLoading(element) {
    if (element) {
      element.innerHTML = `
        <div class="d-flex justify-content-center align-items-center py-4">
          <div class="spinner-border text-primary me-3" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <span class="text-muted">Loading content...</span>
        </div>
      `
    }
  }

  hideLoading(element) {
    if (element) {
      const spinner = element.querySelector('.spinner-border')
      if (spinner) {
        spinner.closest('.d-flex').remove()
      }
    }
  }

  // Smooth reveal animation for dynamic content
  revealContent(element, content) {
    element.style.opacity = '0'
    element.innerHTML = content

    setTimeout(() => {
      element.style.transition = 'opacity 0.3s ease-in-out'
      element.style.opacity = '1'
    }, 50)
  }
}

// Export classes globally for testing
if (typeof window !== 'undefined') {
  window.ThemeManager = ThemeManager
  window.ScrollManager = ScrollManager
  window.ProjectManager = ProjectManager
  window.IconManager = IconManager
  window.AnimationManager = AnimationManager
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const themeManager = new ThemeManager()
  const scrollManager = new ScrollManager()
  const projectManager = new ProjectManager()
  const animationManager = new AnimationManager()
  const iconManager = new IconManager()

  // Preload icon variants for better performance
  iconManager.preloadIcons()

  // Export for potential use by other scripts
  window.portfolioUtils = {
    themeManager,
    scrollManager,
    projectManager,
    animationManager,
    iconManager
  }
})
