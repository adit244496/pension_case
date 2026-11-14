import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

/**
 * The API target and web port can be overridden, e.g. when port 8000 is taken
 * or the API runs on another machine:
 *
 *   PENSION_API=http://127.0.0.1:8001 npm run dev
 *
 * loadEnv only reads .env files, so process.env is consulted first. The port is
 * strict on purpose: drifting to the next free one when 5173 is taken is how a
 * browser ends up on a stale copy of the app that is still answering.
 */
export default defineConfig(({ mode }) => {
  const fileEnv = loadEnv(mode, process.cwd(), '')
  const target = process.env.PENSION_API || fileEnv.PENSION_API || 'http://127.0.0.1:8000'
  const port = Number(process.env.PENSION_WEB_PORT || fileEnv.PENSION_WEB_PORT || 5173)
  return {
    plugins: [react()],
    server: {
      port,
      strictPort: true,
      proxy: { '/api': { target, changeOrigin: true } },
    },
  }
})
