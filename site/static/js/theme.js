/**
 * Modern Theme Manager with ES6+ features
 * Handles dark/light theme switching and back-to-top functionality
 */

class ThemeManager {
  constructor () {
    this.storageKey = 'theme'
    this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    this.currentTheme = this.getInitialTheme()

    this.init()
  }

  getInitialTheme () {
    const saved = localStorage.getItem(this.storageKey)
    return saved || (this.mediaQuery.matches ? 'dark' : 'light')
  }

  setTheme (theme) {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem(this.storageKey, theme)
    this.currentTheme = theme

    // Dispatch custom event for other components
    window.dispatchEvent(
      new CustomEvent('themechange', {
        detail: { theme }
      })
    )
  }

  updateButton (button, theme) {
    const isDark = theme === 'dark'
    button.textContent = isDark ? 'Light' : 'Dark'
    button.classList.toggle('btn-outline-light', isDark)
    button.classList.toggle('btn-outline-dark', !isDark)
    button.setAttribute(
      'aria-label',
      `Switch to ${isDark ? 'light' : 'dark'} theme`
    )
  }

  toggleTheme () {
    const nextTheme = this.currentTheme === 'dark' ? 'light' : 'dark'
    this.setTheme(nextTheme)
    return nextTheme
  }

  init () {
    // Set initial theme
    this.setTheme(this.currentTheme)

    // Setup theme toggle button
    const themeButton = document.getElementById('theme-toggle')
    if (themeButton) {
      this.updateButton(themeButton, this.currentTheme)

      themeButton.addEventListener('click', () => {
        const newTheme = this.toggleTheme()
        this.updateButton(themeButton, newTheme)
      })
    }

    // Listen for system theme changes
    this.mediaQuery.addEventListener('change', (e) => {
      if (!localStorage.getItem(this.storageKey)) {
        const systemTheme = e.matches ? 'dark' : 'light'
        this.setTheme(systemTheme)
        if (themeButton) {
          this.updateButton(themeButton, systemTheme)
        }
      }
    })
  }
}

class ScrollManager {
  constructor () {
    this.threshold = 300
    this.isVisible = false
    this.button = document.getElementById('backToTopBtn')
    this.navHeight = 80 // Approximate navbar height

    if (this.button) {
      this.init()
    }
    this.initSmoothScrolling()
  }

  toggleVisibility () {
    const shouldShow = window.pageYOffset > this.threshold

    if (shouldShow !== this.isVisible) {
      this.isVisible = shouldShow
      this.button.style.display = shouldShow ? 'block' : 'none'
      this.button.setAttribute('aria-hidden', !shouldShow)
    }
  }

  scrollToTop () {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    })

    // Focus management for accessibility
    setTimeout(() => {
      document.querySelector('h1, [tabindex="0"]')?.focus()
    }, 100)
  }

  init () {
    // Use passive listener for better performance
    window.addEventListener(
      'scroll',
      () => {
        requestAnimationFrame(() => this.toggleVisibility())
      },
      { passive: true }
    )

    this.button.addEventListener('click', (e) => {
      e.preventDefault()
      this.scrollToTop()
    })

    // Initial check
    this.toggleVisibility()
  }

  initSmoothScrolling () {
    // Handle internal navigation links
    const internalNavLinks = document.querySelectorAll(
      '.internal-nav[data-scroll]'
    )

    internalNavLinks.forEach((link) => {
      link.addEventListener('click', (e) => {
        e.preventDefault()
        const targetId = link.getAttribute('data-scroll')
        this.scrollToSection(targetId)

        // Update active state
        this.updateActiveNavLink(link)

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

  scrollToSection (targetId) {
    const target = document.getElementById(targetId)
    if (!target) return

    const targetPosition =
      target.getBoundingClientRect().top + window.pageYOffset - this.navHeight

    window.scrollTo({
      top: targetPosition,
      behavior: 'smooth'
    })

    // Update URL without triggering page reload
    history.pushState(null, null, `#${targetId}`)
  }

  updateActiveNavLink (activeLink) {
    // Remove active class from all internal nav links
    document.querySelectorAll('.internal-nav').forEach((link) => {
      link.classList.remove('active')
      link.removeAttribute('aria-current')
    })

    // Add active class to current link
    activeLink.classList.add('active')
    activeLink.setAttribute('aria-current', 'page')
  }

  setupNavigationHighlighting () {
    const sections = document.querySelectorAll('section[id]')

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const currentNavLink = document.querySelector(
              `[data-scroll="${entry.target.id}"]`
            )
            if (currentNavLink) {
              this.updateActiveNavLink(currentNavLink)
            }
          }
        })
      },
      {
        threshold: 0.3,
        rootMargin: `-${this.navHeight}px 0px -50% 0px`
      }
    )

    sections.forEach((section) => observer.observe(section))
  }
}

class ProjectManager {
  constructor () {
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

  init () {
    this.setupEventListeners()
    this.interceptRepoWidget()
  }

  setupEventListeners () {
    // Filter buttons
    const filterButtons = document.querySelectorAll('.filter-btn')
    filterButtons.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        this.setFilter(e.target.getAttribute('data-filter'))
        this.updateFilterButtons(e.target)
      })
    })

    // Sort dropdown
    const sortSelect = document.getElementById('repo-sort')
    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        this.currentSort = e.target.value
        this.applyFiltersAndSort()
      })
    }
  }

  setFilter (filter) {
    this.currentFilter = filter
    this.applyFiltersAndSort()
  }

  updateFilterButtons (activeButton) {
    document.querySelectorAll('.filter-btn').forEach((btn) => {
      btn.classList.remove('active')
      btn.setAttribute('aria-pressed', 'false')
    })

    activeButton.classList.add('active')
    activeButton.setAttribute('aria-pressed', 'true')
  }

  categorizeProject (project) {
    const text = `${project.name} ${project.description || ''}`.toLowerCase()

    for (const [category, keywords] of Object.entries(this.categories)) {
      if (keywords.some((keyword) => text.includes(keyword))) {
        return category
      }
    }
    return 'other'
  }

  filterProjects () {
    if (this.currentFilter === 'all') {
      return this.projects
    }

    return this.projects.filter((project) => {
      const category = this.categorizeProject(project)
      return category === this.currentFilter
    })
  }

  sortProjects (projects) {
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

  applyFiltersAndSort () {
    const filtered = this.filterProjects()
    const sorted = this.sortProjects(filtered)
    this.renderProjects(sorted)
  }

  renderProjects (projects) {
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
      projects.forEach((project) => {
        const card = this.createProjectCard(project)
        projectsRow.appendChild(card)
      })
    }
  }

  createProjectCard (project) {
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

  interceptRepoWidget () {
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

  setupWidgetOverride () {
    const originalCreateRepoWidget = window.createRepoWidget

    window.createRepoWidget = (config) => {
      try {
        // Store the original config
        const originalCallback = config.onLoad || (() => {})

        // Override onLoad to capture data
        config.onLoad = (projects) => {
          this.projects = projects || []
          this.hideLoading()
          this.applyFiltersAndSort()
          originalCallback(projects)
        }

        // Call original function
        return originalCreateRepoWidget(config)
      } catch (error) {
        // eslint-disable-next-line no-console
        console.warn('Error setting up repo widget:', error)
        this.hideLoading()
      }
    }
  }

  hideLoading () {
    const loading = document.getElementById('repo-loading')
    if (loading) {
      loading.style.display = 'none'
    }
  }
}

class AnimationManager {
  constructor () {
    this.animatedElements = new Set()
    this.init()
  }

  init () {
    this.setupScrollAnimations()
    this.animateProgressBars()
    this.setupCardAnimations()
  }

  setupScrollAnimations () {
    const sections = document.querySelectorAll('section')

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('section-animate', 'visible')

            // Animate skills progress bars when skills section comes into view
            if (entry.target.id === 'skills') {
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

    sections.forEach((section) => {
      section.classList.add('section-animate')
      observer.observe(section)
    })
  }

  animateSkillsBars () {
    const progressBars = document.querySelectorAll('#skills .progress-bar')

    progressBars.forEach((bar, index) => {
      const targetWidth = bar.style.width
      bar.style.width = '0%'

      setTimeout(() => {
        bar.style.width = targetWidth
      }, index * 100) // Stagger the animations
    })
  }

  animateProgressBars () {
    const progressBars = document.querySelectorAll('.progress-bar')

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
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

    progressBars.forEach((bar) => observer.observe(bar))
  }

  setupCardAnimations () {
    const cards = document.querySelectorAll('.card')

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('fade-in')
          }
        })
      },
      { threshold: 0.1 }
    )

    cards.forEach((card) => observer.observe(card))
  }

  // Add loading state management
  showLoading (element) {
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

  hideLoading (element) {
    if (element) {
      const spinner = element.querySelector('.spinner-border')
      if (spinner) {
        spinner.closest('.d-flex').remove()
      }
    }
  }

  // Smooth reveal animation for dynamic content
  revealContent (element, content) {
    element.style.opacity = '0'
    element.innerHTML = content

    setTimeout(() => {
      element.style.transition = 'opacity 0.3s ease-in-out'
      element.style.opacity = '1'
    }, 50)
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const themeManager = new ThemeManager()
  const scrollManager = new ScrollManager()
  const projectManager = new ProjectManager()
  const animationManager = new AnimationManager()

  // Export for potential use by other scripts
  window.portfolioUtils = {
    themeManager,
    scrollManager,
    projectManager,
    animationManager
  }
})
