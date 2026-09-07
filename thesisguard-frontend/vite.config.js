import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],

  // ── Dev Server ────────────────────────────────────────────────────────────
  server: {
    port: 5173,
    strictPort: true,   // fail fast if port is occupied
    open: false,        // don't auto-open browser (CI-friendly)
  },

  // ── Production Build Optimisations ───────────────────────────────────────
  build: {
    // Minify with Vite 8's built-in oxc transformer (default, no extra install needed)
    // 'esbuild' and 'terser' are optional peer deps in Vite 8+; oxc is bundled.
    minify: true,

    // Suppress source maps in production (reduces deployed bundle size)
    sourcemap: false,

    // Warn when an individual chunk exceeds 500 kB (helps catch accidental large imports)
    chunkSizeWarningLimit: 500,

    // Enable CSS code splitting — each async chunk gets its own CSS file
    cssCodeSplit: true,

    rollupOptions: {
      output: {
        // Keep React runtime in its own vendor chunk so it can be cached
        // independently of application code changes.
        // NOTE: rolldown (Vite 8) requires manualChunks as a function, not object.
        manualChunks(id) {
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
            return 'react-vendor'
          }
        },
        // Deterministic, human-readable chunk filenames
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },

  },
})

