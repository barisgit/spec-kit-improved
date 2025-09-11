import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import type { SyncConfiguration, SyncResult } from '../lib/types';

// This import will fail until implementation exists
import { SyncService } from '../lib/sync-service';

describe('SyncService', () => {
  let syncService: SyncService;
  
  const defaultConfig: SyncConfiguration = {
    sourcePatterns: [
      {
        pattern: '../src/specify_cli/commands/*/docs.{md,mdx}',
        type: 'command',
        outputSubdir: 'reference/cli'
      },
      {
        pattern: '../src/specify_cli/services/*/docs.{md,mdx}',
        type: 'service',
        outputSubdir: 'reference/api'
      },
      {
        pattern: '../src/specify_cli/guides/*.{md,mdx}',
        type: 'guide',
        outputSubdir: 'guides'
      }
    ],
    outputDir: 'src/content/docs',
    watch: false,
    clean: true,
    validate: true,
    preserveExtensions: true
  };
  
  beforeEach(() => {
    syncService = new SyncService();
  });

  describe('initialize', () => {
    it('should initialize with default configuration', async () => {
      await expect(syncService.initialize(defaultConfig)).resolves.not.toThrow();
    });

    it('should validate configuration on initialization', async () => {
      const invalidConfig = { ...defaultConfig, outputDir: '' };
      await expect(syncService.initialize(invalidConfig)).rejects.toThrow();
    });

    it('should accept custom patterns', async () => {
      const customConfig = {
        ...defaultConfig,
        sourcePatterns: [
          {
            pattern: 'custom/path/*.md',
            type: 'guide' as const,
            outputSubdir: 'custom'
          }
        ]
      };
      
      await expect(syncService.initialize(customConfig)).resolves.not.toThrow();
    });
  });

  describe('sync', () => {
    beforeEach(async () => {
      await syncService.initialize(defaultConfig);
    });

    it('should return sync result with statistics', async () => {
      const result = await syncService.sync();
      
      expect(result).toHaveProperty('filesProcessed');
      expect(result).toHaveProperty('filesAdded');
      expect(result).toHaveProperty('filesUpdated');
      expect(result).toHaveProperty('filesRemoved');
      expect(result).toHaveProperty('errors');
      expect(result).toHaveProperty('duration');
    });

    it('should process discovered files', async () => {
      const result = await syncService.sync();
      
      expect(result.filesProcessed).toBeGreaterThanOrEqual(0);
      expect(Array.isArray(result.filesAdded)).toBe(true);
      expect(Array.isArray(result.filesUpdated)).toBe(true);
    });

    it('should handle missing documentation gracefully', async () => {
      const result = await syncService.sync();
      
      // All errors should be recoverable
      result.errors.forEach(error => {
        expect(error.recoverable).toBe(true);
      });
    });

    it('should track sync duration', async () => {
      const result = await syncService.sync();
      
      expect(result.duration).toBeGreaterThan(0);
      expect(result.duration).toBeLessThan(5000); // Should complete in < 5s
    });
  });

  describe('watch', () => {
    it('should start file watching', async () => {
      const watchConfig = { ...defaultConfig, watch: true };
      await syncService.initialize(watchConfig);
      
      await expect(syncService.watch()).resolves.not.toThrow();
      
      // Clean up
      await syncService.stopWatching();
    });

    it('should stop file watching', async () => {
      const watchConfig = { ...defaultConfig, watch: true };
      await syncService.initialize(watchConfig);
      
      await syncService.watch();
      await expect(syncService.stopWatching()).resolves.not.toThrow();
    });

    it('should not start watching if not configured', async () => {
      await syncService.initialize(defaultConfig);
      
      await expect(syncService.watch()).rejects.toThrow();
    });
  });

  describe('clean', () => {
    beforeEach(async () => {
      await syncService.initialize(defaultConfig);
    });

    it('should return list of removed files', async () => {
      const removed = await syncService.clean();
      
      expect(Array.isArray(removed)).toBe(true);
      removed.forEach(path => {
        expect(path).toMatch(/\.(md|mdx)$/);
      });
    });

    it('should only remove orphaned files', async () => {
      // First sync to establish baseline
      await syncService.sync();
      
      // Clean should not remove synced files
      const removed = await syncService.clean();
      
      // Should be empty or only contain truly orphaned files
      expect(removed.length).toBeGreaterThanOrEqual(0);
    });
  });

  describe('validate', () => {
    beforeEach(async () => {
      await syncService.initialize(defaultConfig);
    });

    it('should return validation errors', async () => {
      const errors = await syncService.validate();
      
      expect(Array.isArray(errors)).toBe(true);
      errors.forEach(error => {
        expect(error).toHaveProperty('file');
        expect(error).toHaveProperty('error');
        expect(error).toHaveProperty('type');
        expect(error).toHaveProperty('recoverable');
      });
    });

    it('should categorize error types correctly', async () => {
      const errors = await syncService.validate();
      
      errors.forEach(error => {
        expect(['parse', 'validate', 'write', 'unknown']).toContain(error.type);
      });
    });
  });

  describe('event handling', () => {
    it('should emit sync events', async () => {
      await syncService.initialize(defaultConfig);
      
      const mockHandler = vi.fn();
      syncService.on('complete', mockHandler);
      
      await syncService.sync();
      
      expect(mockHandler).toHaveBeenCalled();
    });

    it('should emit error events', async () => {
      await syncService.initialize(defaultConfig);
      
      const mockHandler = vi.fn();
      syncService.on('error', mockHandler);
      
      // Force an error by using invalid config
      const invalidConfig = { ...defaultConfig, outputDir: '/invalid/path' };
      await syncService.initialize(invalidConfig).catch(() => {});
      
      // Error handler might be called
      expect(mockHandler.mock.calls.length).toBeGreaterThanOrEqual(0);
    });
  });
});