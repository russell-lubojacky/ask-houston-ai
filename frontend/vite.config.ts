// frontend/vite.config.js
import { sveltekit } from '@sveltejs/kit/vite';

/** @type {import('vite').UserConfig} */
export default {
  plugins: [sveltekit()],
  server: {
    proxy: {
      '/ask': 'http://app:8000' // Proxy backend API to FastAPI container
    }
  }
};