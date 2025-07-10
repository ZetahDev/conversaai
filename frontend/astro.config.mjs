import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwind from '@astrojs/tailwind';
import node from '@astrojs/node';
import { codecovVitePlugin } from '@codecov/vite-plugin';

// https://astro.build/config
export default defineConfig({
  site: 'http://localhost:4321',
  integrations: [
    react(),
    tailwind({
      applyBaseStyles: true,
    }),
  ],
  output: 'server',
  adapter: node({
    mode: 'standalone',
  }),
  server: {
    port: 4321,
    host: true,
  },
  vite: {
    plugins: [
      // Codecov plugin para bundle analysis
      codecovVitePlugin({
        enableBundleAnalysis: process.env.CODECOV_TOKEN !== undefined,
        bundleName: "conversaai-frontend",
        uploadToken: process.env.CODECOV_TOKEN,
      }),
    ],
    resolve: {
      alias: {
        '~': '/src',
        '@': '/src',
      },
    },
    define: {
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
    },
    server: {
      watch: {
        usePolling: true,
      },
    },
  },
  build: {
    assets: '_astro',
  },
  compilerOptions: {
    types: ['astro/client'],
  },
});
