#!/usr/bin/env node

/**
 * Development server with live reload and enhanced features
 * Alternative to live-server with portfolio-specific optimizations
 */

const fs = require('fs')
const path = require('path')
const http = require('http')
const https = require('https')
const { promisify } = require('util')
const mime = require('mime-types')
const chokidar = require('chokidar')
const WebSocket = require('ws')

const readFile = promisify(fs.readFile)
const stat = promisify(fs.stat)

class DevServer {
  constructor(options = {}) {
    this.options = {
      port: options.port || 3000,
      host: options.host || 'localhost',
      root: options.root || './site',
      open: options.open !== false,
      livereload: options.livereload !== false,
      https: options.https || false,
      cors: options.cors !== false,
      ...options
    }
    
    this.clients = new Set()
    this.wss = null
    this.server = null
    this.watcher = null
  }

  /**
   * Start the development server
   */
  async start() {
    try {
      console.log('🚀 Starting development server...')
      
      // Create HTTP/HTTPS server
      if (this.options.https) {
        // Generate self-signed certificate for development
        this.server = https.createServer(this.getHttpsOptions(), this.handleRequest.bind(this))
      } else {
        this.server = http.createServer(this.handleRequest.bind(this))
      }
      
      // Setup WebSocket server for live reload
      if (this.options.livereload) {
        this.setupLiveReload()
      }
      
      // Start server
      await new Promise((resolve, reject) => {
        this.server.listen(this.options.port, this.options.host, (error) => {
          if (error) reject(error)
          else resolve()
        })
      })
      
      // Setup file watcher
      if (this.options.livereload) {
        this.setupFileWatcher()
      }
      
      const protocol = this.options.https ? 'https' : 'http'
      const url = `${protocol}://${this.options.host}:${this.options.port}`
      
      console.log(`✅ Server running at ${url}`)
      console.log(`📁 Serving files from ${path.resolve(this.options.root)}`)
      
      if (this.options.livereload) {
        console.log('🔄 Live reload enabled')
      }
      
      if (this.options.open) {
        this.openBrowser(url)
      }
      
    } catch (error) {
      console.error('❌ Failed to start server:', error)
      process.exit(1)
    }
  }

  /**
   * Handle HTTP requests
   */
  async handleRequest(req, res) {
    try {
      const url = new URL(req.url, `http://${req.headers.host}`)
      let filePath = this.resolveFilePath(url.pathname)
      
      // Handle CORS
      if (this.options.cors) {
        res.setHeader('Access-Control-Allow-Origin', '*')
        res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        
        if (req.method === 'OPTIONS') {
          res.writeHead(200)
          res.end()
          return
        }
      }
      
      // Check if file exists
      if (!fs.existsSync(filePath)) {
        // SPA fallback - serve index.html for non-existent routes
        const indexPath = path.join(path.dirname(filePath), 'index.html')
        if (fs.existsSync(indexPath)) {
          filePath = indexPath
        } else {
          return this.send404(res, url.pathname)
        }
      }
      
      const stats = await stat(filePath)
      
      if (stats.isDirectory()) {
        // Serve index.html from directory
        const indexPath = path.join(filePath, 'index.html')
        if (fs.existsSync(indexPath)) {
          filePath = indexPath
        } else {
          return this.sendDirectoryListing(res, filePath, url.pathname)
        }
      }
      
      // Serve file
      await this.serveFile(res, filePath)
      
    } catch (error) {
      console.error('❌ Request error:', error)
      this.send500(res, error)
    }
  }

  /**
   * Resolve file path from URL
   */
  resolveFilePath(urlPath) {
    const rootPath = path.resolve(this.options.root)
    let filePath = path.join(rootPath, decodeURIComponent(urlPath))
    
    // Prevent directory traversal
    if (!filePath.startsWith(rootPath)) {
      filePath = path.join(rootPath, 'index.html')
    }
    
    return filePath
  }

  /**
   * Serve a file
   */
  async serveFile(res, filePath) {
    const content = await readFile(filePath)
    const mimeType = mime.lookup(filePath) || 'application/octet-stream'
    const stats = await stat(filePath)
    
    res.setHeader('Content-Type', mimeType)
    res.setHeader('Content-Length', stats.size)
    res.setHeader('Last-Modified', stats.mtime.toUTCString())
    
    // Add security headers for HTML files
    if (mimeType === 'text/html') {
      res.setHeader('X-Frame-Options', 'SAMEORIGIN')
      res.setHeader('X-Content-Type-Options', 'nosniff')
      res.setHeader('X-XSS-Protection', '1; mode=block')
      
      // Inject live reload script
      if (this.options.livereload) {
        const htmlContent = content.toString()
        const injectedContent = this.injectLiveReloadScript(htmlContent)
        res.writeHead(200)
        res.end(injectedContent)
        return
      }
    }
    
    res.writeHead(200)
    res.end(content)
  }

  /**
   * Inject live reload script
   */
  injectLiveReloadScript(html) {
    const script = `
    <script>
    (function() {
      const ws = new WebSocket('ws://${this.options.host}:${this.options.port}');
      ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === 'reload') {
          console.log('🔄 Reloading page...');
          window.location.reload();
        }
      };
      ws.onclose = function() {
        console.log('🔌 Live reload disconnected');
      };
    })();
    </script>
    `
    
    // Inject before closing body tag
    return html.replace('</body>', script + '</body>')
  }

  /**
   * Setup WebSocket server for live reload
   */
  setupLiveReload() {
    this.wss = new WebSocket.Server({ server: this.server })
    
    this.wss.on('connection', (ws) => {
      this.clients.add(ws)
      console.log(`🔌 Client connected (${this.clients.size} active)`)
      
      ws.on('close', () => {
        this.clients.delete(ws)
        console.log(`🔌 Client disconnected (${this.clients.size} active)`)
      })
    })
  }

  /**
   * Setup file watcher
   */
  setupFileWatcher() {
    const watchPath = path.resolve(this.options.root)
    
    this.watcher = chokidar.watch(watchPath, {
      ignored: [
        '**/node_modules/**',
        '**/.git/**',
        '**/.*',
        '**/*.log'
      ],
      ignoreInitial: true
    })
    
    this.watcher.on('change', (filePath) => {
      console.log(`📝 File changed: ${path.relative(watchPath, filePath)}`)
      this.broadcastReload()
    })
    
    this.watcher.on('add', (filePath) => {
      console.log(`📄 File added: ${path.relative(watchPath, filePath)}`)
      this.broadcastReload()
    })
    
    this.watcher.on('unlink', (filePath) => {
      console.log(`🗑️  File deleted: ${path.relative(watchPath, filePath)}`)
      this.broadcastReload()
    })
  }

  /**
   * Broadcast reload message to all clients
   */
  broadcastReload() {
    const message = JSON.stringify({ type: 'reload', timestamp: Date.now() })
    
    this.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(message)
      }
    })
  }

  /**
   * Send 404 response
   */
  send404(res, path) {
    const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>404 - Not Found</title>
      <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        h1 { color: #e74c3c; }
      </style>
    </head>
    <body>
      <h1>404 - Page Not Found</h1>
      <p>The requested path <code>${path}</code> could not be found.</p>
      <a href="/">← Go to homepage</a>
    </body>
    </html>
    `
    
    res.setHeader('Content-Type', 'text/html')
    res.writeHead(404)
    res.end(html)
  }

  /**
   * Send 500 response
   */
  send500(res, error) {
    const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>500 - Server Error</title>
      <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        h1 { color: #e74c3c; }
        pre { text-align: left; background: #f8f9fa; padding: 20px; border-radius: 5px; }
      </style>
    </head>
    <body>
      <h1>500 - Server Error</h1>
      <p>An internal server error occurred.</p>
      <pre>${error.stack}</pre>
      <a href="/">← Go to homepage</a>
    </body>
    </html>
    `
    
    res.setHeader('Content-Type', 'text/html')
    res.writeHead(500)
    res.end(html)
  }

  /**
   * Send directory listing
   */
  async sendDirectoryListing(res, dirPath, urlPath) {
    try {
      const files = fs.readdirSync(dirPath)
      const fileList = await Promise.all(
        files.map(async (file) => {
          const filePath = path.join(dirPath, file)
          const stats = await stat(filePath)
          return {
            name: file,
            path: path.join(urlPath, file),
            isDirectory: stats.isDirectory(),
            size: stats.size,
            modified: stats.mtime
          }
        })
      )
      
      // Sort directories first, then files
      fileList.sort((a, b) => {
        if (a.isDirectory && !b.isDirectory) return -1
        if (!a.isDirectory && b.isDirectory) return 1
        return a.name.localeCompare(b.name)
      })
      
      const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Directory listing for ${urlPath}</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 20px; }
          table { width: 100%; border-collapse: collapse; }
          th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
          .directory { font-weight: bold; }
        </style>
      </head>
      <body>
        <h1>Directory listing for ${urlPath}</h1>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Size</th>
              <th>Modified</th>
            </tr>
          </thead>
          <tbody>
            ${fileList.map(file => `
              <tr>
                <td>
                  <a href="${file.path}" class="${file.isDirectory ? 'directory' : ''}">
                    ${file.isDirectory ? '📁' : '📄'} ${file.name}
                  </a>
                </td>
                <td>${file.isDirectory ? '-' : this.formatFileSize(file.size)}</td>
                <td>${file.modified.toISOString().split('T')[0]}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </body>
      </html>
      `
      
      res.setHeader('Content-Type', 'text/html')
      res.writeHead(200)
      res.end(html)
      
    } catch (error) {
      this.send500(res, error)
    }
  }

  /**
   * Format file size
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  /**
   * Open browser
   */
  openBrowser(url) {
    const start = process.platform === 'darwin' ? 'open' : 
                  process.platform === 'win32' ? 'start' : 'xdg-open'
    
    require('child_process').exec(`${start} ${url}`)
  }

  /**
   * Get HTTPS options
   */
  getHttpsOptions() {
    // For development, you might want to generate or provide SSL certificates
    // This is a basic self-signed cert setup
    return {
      // key: fs.readFileSync('dev-cert/key.pem'),
      // cert: fs.readFileSync('dev-cert/cert.pem')
    }
  }

  /**
   * Stop the server
   */
  async stop() {
    console.log('🛑 Stopping development server...')
    
    if (this.watcher) {
      await this.watcher.close()
    }
    
    if (this.wss) {
      this.wss.close()
    }
    
    if (this.server) {
      await new Promise((resolve) => {
        this.server.close(resolve)
      })
    }
    
    console.log('✅ Server stopped')
  }
}

// CLI usage
if (require.main === module) {
  const args = process.argv.slice(2)
  const options = {}
  
  // Parse CLI arguments (support both --key=value and --key value formats)
  for (let i = 0; i < args.length; i++) {
    const arg = args[i]

    // Handle --key=value format
    if (arg.includes('=')) {
      const [key, value] = arg.split('=', 2)
      switch (key) {
        case '--port':
          options.port = parseInt(value)
          break
        case '--host':
          options.host = value
          break
        case '--root':
          options.root = value
          break
      }
      continue
    }

    // Handle --key value format
    switch (arg) {
      case '--port':
      case '-p':
        options.port = parseInt(args[++i])
        break
      case '--host':
      case '-h':
        options.host = args[++i]
        break
      case '--root':
      case '-r':
        options.root = args[++i]
        break
      case '--no-open':
        options.open = false
        break
      case '--no-livereload':
        options.livereload = false
        break
      case '--https':
        options.https = true
        break
      case '--no-cors':
        options.cors = false
        break
    }
  }
  
  const server = new DevServer(options)
  
  // Handle graceful shutdown
  process.on('SIGINT', async () => {
    await server.stop()
    process.exit(0)
  })
  
  process.on('SIGTERM', async () => {
    await server.stop()
    process.exit(0)
  })
  
  server.start()
}

module.exports = DevServer