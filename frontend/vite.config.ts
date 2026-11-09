import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// 개발 중엔 /api, /uploads 요청을 FastAPI(8000)로 넘겨서 CORS 신경 쓸 필요 없게 함
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/uploads': 'http://localhost:8000',
    },
  },
})
