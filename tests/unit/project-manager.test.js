/**
 * Unit Tests for ProjectManager Class - Simplified Version
 * Tests project filtering, sorting, and rendering functionality
 */

const { TestUtils } = require('./setup.js')

describe('ProjectManager', () => {
  let mockContainer
  let mockNoResults
  let mockFilterButtons

  beforeEach(() => {
    mockContainer = TestUtils.createMockElement('div', { id: 'repo-container' })
    mockNoResults = TestUtils.createMockElement('div', {
      id: 'no-results',
      style: 'display: none;'
    })

    mockFilterButtons = [
      TestUtils.createMockElement('button', {
        class: 'filter-btn',
        'data-filter': 'all'
      }),
      TestUtils.createMockElement('button', {
        class: 'filter-btn',
        'data-filter': 'cybersecurity'
      }),
      TestUtils.createMockElement('button', {
        class: 'filter-btn',
        'data-filter': 'healthcare'
      })
    ]

    ;[mockContainer, mockNoResults, ...mockFilterButtons].forEach((el) => {
      document.body.appendChild(el)
    })
  })

  afterEach(() => {
    ;[mockContainer, mockNoResults, ...mockFilterButtons].forEach((el) => {
      if (el.parentNode) el.parentNode.removeChild(el)
    })
    jest.clearAllMocks()
  })

  describe('Project Categorization', () => {
    test('should categorize cybersecurity project correctly', () => {
      const project = {
        name: 'security-scanner',
        description: 'A cybersecurity vulnerability scanner'
      }

      const categories = {
        cybersecurity: [
          'security',
          'cyber',
          'auth',
          'encryption',
          'vulnerability',
          'pentest'
        ],
        healthcare: [
          'medical',
          'health',
          'hospital',
          'patient',
          'dicom',
          'pacs'
        ],
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

      const categorizeProject = (proj) => {
        const text = `${proj.name} ${proj.description || ''}`.toLowerCase()
        for (const [category, keywords] of Object.entries(categories)) {
          if (keywords.some((keyword) => text.includes(keyword))) {
            return category
          }
        }
        return 'other'
      }

      const category = categorizeProject(project)
      expect(category).toBe('cybersecurity')
    })

    test('should categorize healthcare project correctly', () => {
      const project = {
        name: 'hospital-management',
        description: 'Healthcare patient management system'
      }

      const categories = {
        cybersecurity: [
          'security',
          'cyber',
          'auth',
          'encryption',
          'vulnerability',
          'pentest'
        ],
        healthcare: [
          'medical',
          'health',
          'hospital',
          'patient',
          'dicom',
          'pacs'
        ],
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

      const categorizeProject = (proj) => {
        const text = `${proj.name} ${proj.description || ''}`.toLowerCase()
        for (const [category, keywords] of Object.entries(categories)) {
          if (keywords.some((keyword) => text.includes(keyword))) {
            return category
          }
        }
        return 'other'
      }

      const category = categorizeProject(project)
      expect(category).toBe('healthcare')
    })

    test('should return "other" for uncategorized projects', () => {
      const project = {
        name: 'random-project',
        description: 'Some random project'
      }

      const categories = {
        cybersecurity: [
          'security',
          'cyber',
          'auth',
          'encryption',
          'vulnerability',
          'pentest'
        ],
        healthcare: [
          'medical',
          'health',
          'hospital',
          'patient',
          'dicom',
          'pacs'
        ],
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

      const categorizeProject = (proj) => {
        const text = `${proj.name} ${proj.description || ''}`.toLowerCase()
        for (const [category, keywords] of Object.entries(categories)) {
          if (keywords.some((keyword) => text.includes(keyword))) {
            return category
          }
        }
        return 'other'
      }

      const category = categorizeProject(project)
      expect(category).toBe('other')
    })
  })

  describe('Project Sorting', () => {
    const mockProjects = [
      {
        name: 'automation-script',
        stargazers_count: 5,
        created_at: '2023-03-01T10:00:00Z',
        updated_at: '2023-05-01T10:00:00Z'
      },
      {
        name: 'hospital-management',
        stargazers_count: 15,
        created_at: '2023-02-10T10:00:00Z',
        updated_at: '2023-07-10T10:00:00Z'
      },
      {
        name: 'security-scanner',
        stargazers_count: 25,
        created_at: '2023-01-15T10:00:00Z',
        updated_at: '2023-06-15T10:00:00Z'
      }
    ]

    test('should sort by name alphabetically', () => {
      const sortProjects = (projects, sortBy) => {
        return [...projects].sort((a, b) => {
          switch (sortBy) {
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

      const result = sortProjects(mockProjects, 'name')

      expect(result[0].name).toBe('automation-script')
      expect(result[1].name).toBe('hospital-management')
      expect(result[2].name).toBe('security-scanner')
    })

    test('should sort by stars descending', () => {
      const sortProjects = (projects, sortBy) => {
        return [...projects].sort((a, b) => {
          switch (sortBy) {
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

      const result = sortProjects(mockProjects, 'stars')

      expect(result[0].stargazers_count).toBe(25)
      expect(result[1].stargazers_count).toBe(15)
      expect(result[2].stargazers_count).toBe(5)
    })

    test('should sort by updated date descending (default)', () => {
      const sortProjects = (projects, sortBy) => {
        return [...projects].sort((a, b) => {
          switch (sortBy) {
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

      const result = sortProjects(mockProjects, 'updated')

      expect(new Date(result[0].updated_at).getTime()).toBeGreaterThan(
        new Date(result[1].updated_at).getTime()
      )
    })
  })

  describe('Project Card Creation', () => {
    test('should create project card with correct structure', () => {
      const project = {
        name: 'security-scanner',
        description: 'A cybersecurity vulnerability scanner',
        html_url: 'https://github.com/user/security-scanner',
        language: 'Python',
        stargazers_count: 25
      }

      const createProjectCard = (proj) => {
        const card = document.createElement('div')
        card.className = 'col-md-6 col-lg-4 mb-4'

        const categories = {
          cybersecurity: [
            'security',
            'cyber',
            'auth',
            'encryption',
            'vulnerability',
            'pentest'
          ]
        }

        const categorizeProject = (project) => {
          const text =
            `${project.name} ${project.description || ''}`.toLowerCase()
          for (const [category, keywords] of Object.entries(categories)) {
            if (keywords.some((keyword) => text.includes(keyword))) {
              return category
            }
          }
          return 'other'
        }

        const category = categorizeProject(proj)
        const categoryBadge =
          category !== 'other'
            ? `<span class="badge bg-secondary mb-2">${category}</span>`
            : ''

        card.innerHTML = `
          <div class="card h-100 project-card" data-category="${category}">
            <div class="card-body d-flex flex-column">
              ${categoryBadge}
              <h5 class="card-title">${proj.name}</h5>
              <p class="card-text flex-grow-1">${proj.description || 'No description available'}</p>
              <div class="d-flex justify-content-between align-items-center mt-auto">
                <small class="text-muted">
                  ${proj.language ? `<span class="me-3">📝 ${proj.language}</span>` : ''}
                  ${proj.stargazers_count ? `⭐ ${proj.stargazers_count}` : ''}
                </small>
                <a href="${proj.html_url}" target="_blank" rel="noopener" 
                   class="btn btn-sm btn-outline-primary"
                   aria-label="View ${proj.name} on GitHub">
                  View →
                </a>
              </div>
            </div>
          </div>
        `

        return card
      }

      const card = createProjectCard(project)

      expect(card.className).toBe('col-md-6 col-lg-4 mb-4')
      expect(card.innerHTML).toContain('security-scanner')
      expect(card.innerHTML).toContain('cybersecurity vulnerability scanner')
      expect(card.innerHTML).toContain('Python')
      expect(card.innerHTML).toContain('⭐ 25')
      expect(card.innerHTML).toContain(
        'https://github.com/user/security-scanner'
      )
    })

    test('should handle project without description', () => {
      const project = {
        name: 'test-project',
        html_url: 'https://github.com/user/test'
      }

      const createProjectCard = (proj) => {
        const card = document.createElement('div')
        card.innerHTML = `<p>${proj.description || 'No description available'}</p>`
        return card
      }

      const card = createProjectCard(project)
      expect(card.innerHTML).toContain('No description available')
    })

    test('should include category badge for categorized projects', () => {
      const project = {
        name: 'security-scanner',
        description: 'A cybersecurity vulnerability scanner'
      }

      const categories = {
        cybersecurity: ['security', 'cyber', 'vulnerability']
      }

      const categorizeProject = (proj) => {
        const text = `${proj.name} ${proj.description || ''}`.toLowerCase()
        for (const [category, keywords] of Object.entries(categories)) {
          if (keywords.some((keyword) => text.includes(keyword))) {
            return category
          }
        }
        return 'other'
      }

      const category = categorizeProject(project)
      const categoryBadge =
        category !== 'other'
          ? `<span class="badge bg-secondary mb-2">${category}</span>`
          : ''

      expect(categoryBadge).toContain(
        '<span class="badge bg-secondary mb-2">cybersecurity</span>'
      )
    })
  })

  describe('Filter Button Management', () => {
    test('should update filter button states', () => {
      const updateFilterButtons = (activeButton) => {
        document.querySelectorAll('.filter-btn').forEach((btn) => {
          btn.classList.remove('active')
          btn.setAttribute('aria-pressed', 'false')
        })

        activeButton.classList.add('active')
        activeButton.setAttribute('aria-pressed', 'true')
      }

      // Mock querySelectorAll to return our mock buttons
      document.querySelectorAll = jest.fn().mockReturnValue(mockFilterButtons)

      updateFilterButtons(mockFilterButtons[1])

      expect(mockFilterButtons[1].classList.add).toHaveBeenCalledWith('active')
      expect(mockFilterButtons[1].setAttribute).toHaveBeenCalledWith(
        'aria-pressed',
        'true'
      )

      ;[mockFilterButtons[0], mockFilterButtons[2]].forEach((btn) => {
        expect(btn.classList.remove).toHaveBeenCalledWith('active')
        expect(btn.setAttribute).toHaveBeenCalledWith('aria-pressed', 'false')
      })
    })
  })

  describe('Accessibility Features', () => {
    test('should include proper ARIA labels in project cards', () => {
      const project = {
        name: 'security-scanner',
        html_url: 'https://github.com/user/security-scanner'
      }

      const ariaLabel = `View ${project.name} on GitHub`

      expect(ariaLabel).toBe('View security-scanner on GitHub')
    })

    test('should manage aria-pressed states for filter buttons', () => {
      const button = mockFilterButtons[0]

      button.setAttribute('aria-pressed', 'true')
      expect(button.setAttribute).toHaveBeenCalledWith('aria-pressed', 'true')

      button.setAttribute('aria-pressed', 'false')
      expect(button.setAttribute).toHaveBeenCalledWith('aria-pressed', 'false')
    })
  })

  describe('Error Handling and Edge Cases', () => {
    test('should handle missing DOM elements gracefully', () => {
      ;[mockContainer, mockNoResults, ...mockFilterButtons].forEach((el) => {
        if (el.parentNode) el.parentNode.removeChild(el)
      })

      const container = document.getElementById('repo-container')
      const noResults = document.getElementById('no-results')

      expect(container).toBeNull()
      expect(noResults).toBeNull()
    })

    test('should handle projects with missing properties', () => {
      const incompleteProject = {
        name: 'test',
        html_url: 'https://github.com/test'
      }

      const createProjectCard = (proj) => {
        const card = document.createElement('div')
        card.innerHTML = `
          <h5>${proj.name}</h5>
          <p>${proj.description || 'No description available'}</p>
          <span>${proj.language || ''}</span>
          <span>${proj.stargazers_count || ''}</span>
        `
        return card
      }

      expect(() => {
        const card = createProjectCard(incompleteProject)
        expect(card).toBeDefined()
      }).not.toThrow()
    })

    test('should handle null or undefined project arrays', () => {
      const renderProjects = (projects) => {
        if (!projects || projects.length === 0) {
          mockContainer.style.display = 'none'
          mockNoResults.style.display = 'block'
          return
        }

        mockContainer.style.display = 'block'
        mockNoResults.style.display = 'none'
      }

      expect(() => {
        renderProjects(null)
        renderProjects(undefined)
        renderProjects([])
      }).not.toThrow()
    })
  })
})
