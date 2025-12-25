import { defineConfig } from "vite";

export default defineConfig({
  server: {
    // TAMBAHAN 1: Izinkan akses dari Network (iPhone)
    host: "0.0.0.0", 
    
    // TAMBAHAN 2: Pastikan port proxy sesuai dengan Backend Anda
    // Jika backend Anda jalan di port 8000, ubah 5000 menjadi 8000 di bawah ini.
    proxy: {
      "/api": {
        target: "http://localhost:5000", // Cek terminal backend, biasanya port 8000
        changeOrigin: true,
        secure: false,
      },
      "/client-assets": {
        target: "http://localhost:5000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});