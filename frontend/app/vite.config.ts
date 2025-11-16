import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig(async () => ({
  plugins: [react(), tailwindcss()],

  // Use relative paths for web deployment
  base: './',

  // Path aliases
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },

  // Standard Vite configuration
  clearScreen: false,
  server: {
    port: 3000,  // Standard React dev server port
    strictPort: true,
    hmr: {
      port: 3001,
    },
  },
  
  build: {
    outDir: 'dist',
    // Exclude Electron-specific code from web build
    rollupOptions: {
      external: (id) => {
        // Don't bundle Node.js modules or Electron modules
        return id.startsWith('electron') || 
               id === 'fs' || 
               id === 'fs-extra' ||
               id === 'path' ||
               id === 'fluent-ffmpeg' ||
               id.startsWith('child_process');
      },
    },
  },
  
  // Optimize dependencies for browser
  optimizeDeps: {
    exclude: ['electron', 'fs', 'fs-extra', 'path', 'fluent-ffmpeg'],
  },
}));
