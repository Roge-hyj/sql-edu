import { defineConfig } from "vite";
import uni from "@dcloudio/vite-plugin-uni";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [uni()],
  server: {
    // 允许局域网访问
    host: "0.0.0.0", 
    port: 5173,
    // --- 新增配置：确保端口不会被随意更改，并强制 HMR 使用物理 IP ---
    strictPort: true,
    hmr: {
    // 删掉之前的硬编码 IP，改用这种方式，或者干脆删掉整个 hmr 块让它自动识别
    protocol: 'ws',
    host: 'localhost' 
  },
    // --- 核心配置：跨域代理 ---
    proxy: {
      "/api": {
        // 在镜像模式下，127.0.0.1 同样指向你的 Windows 宿主机后端
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});