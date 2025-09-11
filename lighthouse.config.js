module.exports = {
  ci: {
    collect: {
      url: [
        'http://localhost:3000/',
        'http://localhost:3000/hermes.html',
        'http://localhost:3000/scania.html',
        'http://localhost:3000/market-analysis.html'
      ],
      settings: {
        chromeFlags: '--no-sandbox --disable-dev-shm-usage'
      }
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 1.0 }],
        'categories:best-practices': ['error', { minScore: 0.9 }],
        'categories:seo': ['error', { minScore: 0.9 }],
        'categories:pwa': ['warn', { minScore: 0.8 }]
      }
    },
    upload: {
      target: 'temporary-public-storage'
    }
  }
}