import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/**',
        '**/*.config.ts',
        '**/*.test.ts',
        'build/**'
      ]
    },
    include: ['scripts/**/*.test.ts'],
    testTimeout: 10000
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './scripts')
    }
  }
});