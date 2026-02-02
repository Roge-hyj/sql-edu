import { defineConfig } from "vite";
import uni from "@dcloudio/vite-plugin-uni";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [uni()],
  server: {
    // 允许局域网访问
    host: "0.0.0.0", 
    port: 5173,
    // --- 核心配置：跨域代理 ---
    proxy: {
      "/api": {
        // 指向你的 FastAPI 后端地址
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        // 把前端发出的 /api/auth/login -> 转发为后端的 /auth/login
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});