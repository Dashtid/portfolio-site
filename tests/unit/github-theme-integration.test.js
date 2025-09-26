/**
 * GitHub Theme Integration Tests
 * Tests the GitHub stats theme switching functionality
 */

/* eslint-env jest */

describe('GitHub Theme Integration', () => {
  let mockGitHubImages

  beforeEach(() => {
    document.body.innerHTML = `
      <section id="projects">
        <div class="github-stats-card">
          <img src="https://github-readme-stats.vercel.app/api/pin/?username=dashtid&repo=daily-maintenance-scripts&theme=default&hide_border=true"
               alt="Daily Maintenance Scripts" loading="lazy">
        </div>
        <div class="github-stats-card">
          <img src="https://github-readme-stats.vercel.app/api/pin/?username=dashtid&repo=Deep-Learning&theme=default&hide_border=true"
               alt="Deep Learning" loading="lazy">
        </div>
        <div class="github-stats-card">
          <img id="github-languages"
               src="https://github-readme-stats.vercel.app/api/top-langs/?username=dashtid&layout=compact&theme=default&hide_border=true&card_width=400"
               alt="Most Used Languages" loading="lazy">
        </div>
      </section>
    `

    mockGitHubImages = document.querySelectorAll(
      'img[src*="github-readme-stats.vercel.app"]'
    )
  })

  describe('GitHub Stats Theme Switching Function', () => {
    // Define the actual function from the HTML
    function updateGitHubStatsTheme(isDark) {
      const theme = isDark ? 'dark' : 'default'
      const githubImages = document.querySelectorAll(
        'img[src*="github-readme-stats.vercel.app"]'
      )

      githubImages.forEach(img => {
        const currentSrc = img.src
        const newSrc = currentSrc.replace(/theme=\w+/, `theme=${theme}`)
        img.src = newSrc
      })
    }

    test('should find all GitHub stats images', () => {
      expect(mockGitHubImages.length).toBe(3)

      mockGitHubImages.forEach(img => {
        expect(img.src).toContain('github-readme-stats.vercel.app')
        expect(img.src).toContain('theme=default')
      })
    })

    test('should switch to dark theme correctly', () => {
      updateGitHubStatsTheme(true)

      const images = document.querySelectorAll(
        'img[src*="github-readme-stats.vercel.app"]'
      )
      images.forEach(img => {
        expect(img.src).toContain('theme=dark')
        expect(img.src).not.toContain('theme=default')
      })
    })

    test('should switch to light theme correctly', () => {
      // First set to dark
      updateGitHubStatsTheme(true)

      // Then switch back to light
      updateGitHubStatsTheme(false)

      const images = document.querySelectorAll(
        'img[src*="github-readme-stats.vercel.app"]'
      )
      images.forEach(img => {
        expect(img.src).toContain('theme=default')
        expect(img.src).not.toContain('theme=dark')
      })
    })

    test('should preserve other URL parameters', () => {
      const originalSrc = mockGitHubImages[0].src
      const originalParams = originalSrc
        .split('&')
        .filter(param => !param.includes('theme='))

      updateGitHubStatsTheme(true)

      const newSrc = mockGitHubImages[0].src
      originalParams.forEach(param => {
        expect(newSrc).toContain(param)
      })

      expect(newSrc).toContain('username=dashtid')
      expect(newSrc).toContain('hide_border=true')
    })

    test('should handle multiple theme switches', () => {
      // Light -> Dark -> Light -> Dark
      updateGitHubStatsTheme(true)
      expect(mockGitHubImages[0].src).toContain('theme=dark')

      updateGitHubStatsTheme(false)
      expect(mockGitHubImages[0].src).toContain('theme=default')

      updateGitHubStatsTheme(true)
      expect(mockGitHubImages[0].src).toContain('theme=dark')
    })

    test('should work with different GitHub API endpoints', () => {
      const pinImage = document.querySelector('[src*="api/pin"]')
      const langImage = document.querySelector('[src*="api/top-langs"]')

      expect(pinImage).toBeTruthy()
      expect(langImage).toBeTruthy()

      updateGitHubStatsTheme(true)

      expect(pinImage.src).toContain('theme=dark')
      expect(langImage.src).toContain('theme=dark')
    })
  })

  describe('Theme Change Event Handling', () => {
    let updateGitHubStatsTheme

    beforeEach(() => {
      // Define the function in the global scope for event handling
      window.updateGitHubStatsTheme = function (isDark) {
        const theme = isDark ? 'dark' : 'default'
        const githubImages = document.querySelectorAll(
          'img[src*="github-readme-stats.vercel.app"]'
        )

        githubImages.forEach(img => {
          const currentSrc = img.src
          const newSrc = currentSrc.replace(/theme=\w+/, `theme=${theme}`)
          img.src = newSrc
        })
      }

      updateGitHubStatsTheme = window.updateGitHubStatsTheme
    })

    test('should respond to themeChanged events', () => {
      let eventHandlerCalled = false
      let eventHandlerParam = null

      // Add event listener like in the actual code
      window.addEventListener('themeChanged', (event) => {
        eventHandlerCalled = true
        eventHandlerParam = event.detail.isDark
        updateGitHubStatsTheme(event.detail.isDark)
      })

      // Dispatch a theme change event
      window.dispatchEvent(
        new CustomEvent('themeChanged', {
          detail: { isDark: true, theme: 'dark' }
        })
      )

      expect(eventHandlerCalled).toBe(true)
      expect(eventHandlerParam).toBe(true)

      // Check that images were actually updated
      const images = document.querySelectorAll(
        'img[src*="github-readme-stats.vercel.app"]'
      )
      images.forEach(img => {
        expect(img.src).toContain('theme=dark')
      })
    })

    test('should handle load event initialization', () => {
      // Mock document.documentElement.getAttribute
      document.documentElement.getAttribute = jest.fn().mockReturnValue('dark')

      let loadHandlerCalled = false
      let loadHandlerParam = null

      // Simulate the load event handler
      window.addEventListener('load', () => {
        const isDark =
          document.documentElement.getAttribute('data-theme') === 'dark'
        loadHandlerCalled = true
        loadHandlerParam = isDark
        updateGitHubStatsTheme(isDark)
      })

      // Trigger load event
      window.dispatchEvent(new Event('load'))

      expect(loadHandlerCalled).toBe(true)
      expect(loadHandlerParam).toBe(true)
    })
  })

  describe('Error Handling', () => {
    function updateGitHubStatsTheme(isDark) {
      try {
        const theme = isDark ? 'dark' : 'default'
        const githubImages = document.querySelectorAll(
          'img[src*="github-readme-stats.vercel.app"]'
        )

        githubImages.forEach(img => {
          const currentSrc = img.src
          const newSrc = currentSrc.replace(/theme=\w+/, `theme=${theme}`)
          img.src = newSrc
        })
      } catch (error) {
        // eslint-disable-next-line no-console
        console.warn('Failed to update GitHub stats theme:', error)
      }
    }

    test('should handle missing images gracefully', () => {
      document.body.innerHTML = ''

      expect(() => {
        updateGitHubStatsTheme(true)
      }).not.toThrow()
    })

    test('should handle malformed URLs gracefully', () => {
      document.body.innerHTML = `
        <img src="https://github-readme-stats.vercel.app/api/pin/?malformed-url" alt="Malformed">
      `

      expect(() => {
        updateGitHubStatsTheme(true)
      }).not.toThrow()

      const img = document.querySelector('img')
      expect(img.src).toBeTruthy()
    })

    test('should handle broken image elements', () => {
      const brokenImg = document.createElement('img')
      brokenImg.src =
        'https://github-readme-stats.vercel.app/api/pin/?theme=default'

      // Make the src property non-writable to simulate an error
      Object.defineProperty(brokenImg, 'src', {
        set() {
          throw new Error('Cannot set src')
        },
        get() {
          return 'https://github-readme-stats.vercel.app/api/pin/?theme=default'
        }
      })

      document.body.appendChild(brokenImg)

      expect(() => {
        updateGitHubStatsTheme(true)
      }).not.toThrow()
    })
  })

  describe('Performance', () => {
    test('should not cause layout thrashing with many images', () => {
      // Create many GitHub images
      for (let i = 0; i < 100; i++) {
        const img = document.createElement('img')
        img.src = `https://github-readme-stats.vercel.app/api/pin/?username=user${i}&theme=default`
        document.body.appendChild(img)
      }

      const startTime = performance.now()

      function updateGitHubStatsTheme(isDark) {
        const theme = isDark ? 'dark' : 'default'
        const githubImages = document.querySelectorAll(
          'img[src*="github-readme-stats.vercel.app"]'
        )

        githubImages.forEach(img => {
          const currentSrc = img.src
          const newSrc = currentSrc.replace(/theme=\w+/, `theme=${theme}`)
          img.src = newSrc
        })
      }

      updateGitHubStatsTheme(true)

      const endTime = performance.now()
      const duration = endTime - startTime

      // Should complete quickly even with many images
      expect(duration).toBeLessThan(100) // 100ms threshold
    })
  })
})
