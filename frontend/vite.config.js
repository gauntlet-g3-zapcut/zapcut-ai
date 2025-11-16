import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import { createReadStream, statSync, existsSync, cpSync } from 'fs'

// Plugin to serve Electron app's dist folder at /editor-app
function serveEditorApp() {
  return {
    name: 'serve-editor-app',
    configureServer(server) {
      const editorDistPath = resolve(__dirname, 'app/dist')
      
      server.middlewares.use('/editor-app', (req, res, next) => {
        // Remove /editor-app prefix and get the file path
        let filePath = req.url.replace('/editor-app', '') || '/index.html'
        if (filePath === '/') filePath = '/index.html'
        
        const fullPath = resolve(editorDistPath, filePath.replace(/^\//, ''))
        
        // Security check: ensure file is within editorDistPath
        if (!fullPath.startsWith(editorDistPath)) {
          res.statusCode = 403
          return res.end('Forbidden')
        }
        
        // Try to serve the file
        try {
          const stats = statSync(fullPath)
          if (stats.isFile()) {
            // Simple MIME type detection
            const ext = fullPath.split('.').pop()?.toLowerCase()
            const mimeTypes = {
              'html': 'text/html',
              'js': 'application/javascript',
              'css': 'text/css',
              'json': 'application/json',
              'png': 'image/png',
              'jpg': 'image/jpeg',
              'jpeg': 'image/jpeg',
              'svg': 'image/svg+xml',
              'ico': 'image/x-icon'
            }
            const mimeType = mimeTypes[ext] || 'application/octet-stream'
            res.setHeader('Content-Type', mimeType)
            createReadStream(fullPath).pipe(res)
            return
          }
        } catch (e) {
          // File doesn't exist, return 404
          res.statusCode = 404
          return res.end('Not Found')
        }
        
        next()
      })
    },
    // Copy app/dist to build output during production builds
    writeBundle() {
      const editorDistPath = resolve(__dirname, 'app/dist')
      const buildOutputPath = resolve(__dirname, 'dist/editor-app')
      
      if (existsSync(editorDistPath)) {
        cpSync(editorDistPath, buildOutputPath, { recursive: true })
        console.log(`✓ Copied app/dist to dist/editor-app`)
      } else {
        console.warn(`⚠ app/dist not found at ${editorDistPath}. Make sure to build the app first.`)
      }
    }
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), serveEditorApp()],
  publicDir: 'public',
  server: {
    fs: {
      // Allow serving files from the Electron app directory
      allow: ['..']
    }
  }
})
