/**
 * Contract tests for the documentation synchronization service
 * These tests MUST be written before implementation (TDD)
 * They should fail initially and pass once implementation is complete
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import type {
  ISyncService,
  IFileDiscovery,
  IFrontmatterProcessor,
  IPathMapper,
  SyncConfiguration,
  DEFAULT_CONFIG
} from './sync-service';

describe('SyncService Contract Tests', () => {
  let syncService: ISyncService;
  
  beforeEach(() => {
    // This will fail until implementation exists
    // syncService = new SyncService();
  });

  describe('Initialization', () => {
    it('should initialize with default configuration', async () => {
      await expect(syncService.initialize(DEFAULT_CONFIG)).resolves.not.toThrow();
    });

    it('should validate configuration on initialization', async () => {
      const invalidConfig = { ...DEFAULT_CONFIG, outputDir: '' };
      await expect(syncService.initialize(invalidConfig as any)).rejects.toThrow();
    });
  });

  describe('Synchronization', () => {
    it('should discover and sync all documentation files', async () => {
      await syncService.initialize(DEFAULT_CONFIG);
      const result = await syncService.sync();
      
      expect(result.filesProcessed).toBeGreaterThanOrEqual(0);
      expect(result.errors).toEqual([]);
      expect(result.duration).toBeGreaterThan(0);
    });

    it('should handle missing documentation files gracefully', async () => {
      await syncService.initialize(DEFAULT_CONFIG);
      const result = await syncService.sync();
      
      expect(result.errors.filter(e => e.recoverable)).toEqual(result.errors);
    });

    it('should update existing files when content changes', async () => {
      await syncService.initialize(DEFAULT_CONFIG);
      const firstSync = await syncService.sync();
      const secondSync = await syncService.sync();
      
      expect(secondSync.filesUpdated.length).toBeLessThanOrEqual(firstSync.filesProcessed);
    });
  });

  describe('File Watching', () => {
    it('should start and stop watching for changes', async () => {
      await syncService.initialize({ ...DEFAULT_CONFIG, watch: true });
      
      await expect(syncService.watch()).resolves.not.toThrow();
      await expect(syncService.stopWatching()).resolves.not.toThrow();
    });

    it('should emit events when files change during watch', async () => {
      const mockHandler = vi.fn();
      await syncService.initialize({ ...DEFAULT_CONFIG, watch: true });
      
      // Test will need event emitter implementation
      // syncService.on('file-updated', mockHandler);
      
      await syncService.watch();
      // Trigger file change
      // expect(mockHandler).toHaveBeenCalled();
      await syncService.stopWatching();
    });
  });

  describe('Cleanup', () => {
    it('should remove orphaned documentation files', async () => {
      await syncService.initialize(DEFAULT_CONFIG);
      const removed = await syncService.clean();
      
      expect(Array.isArray(removed)).toBe(true);
      removed.forEach(path => {
        expect(path).toMatch(/\.mdx?$/);
      });
    });
  });

  describe('Validation', () => {
    it('should validate all documentation files', async () => {
      await syncService.initialize(DEFAULT_CONFIG);
      const errors = await syncService.validate();
      
      expect(Array.isArray(errors)).toBe(true);
      errors.forEach(error => {
        expect(error.file).toBeTruthy();
        expect(error.type).toMatch(/^(parse|validate|write|unknown)$/);
      });
    });
  });
});

describe('FileDiscovery Contract Tests', () => {
  let fileDiscovery: IFileDiscovery;

  beforeEach(() => {
    // This will fail until implementation exists
    // fileDiscovery = new FileDiscovery();
  });

  describe('File Discovery', () => {
    it('should discover files matching patterns', async () => {
      const patterns = DEFAULT_CONFIG.sourcePatterns;
      const files = await fileDiscovery.discoverFiles(patterns);
      
      expect(Array.isArray(files)).toBe(true);
      files.forEach(file => {
        expect(file).toMatch(/\.(md|mdx)$/);
      });
    });

    it('should correctly identify file types', () => {
      const patterns = DEFAULT_CONFIG.sourcePatterns;
      
      const commandFile = 'src/specify_cli/commands/init/docs.mdx';
      expect(fileDiscovery.getFileType(commandFile, patterns)).toBe('command');
      
      const serviceFile = 'src/specify_cli/services/template/docs.md';
      expect(fileDiscovery.getFileType(serviceFile, patterns)).toBe('service');
      
      const guideFile = 'src/specify_cli/guides/getting-started.mdx';
      expect(fileDiscovery.getFileType(guideFile, patterns)).toBe('guide');
    });

    it('should extract names from file paths', () => {
      expect(fileDiscovery.extractName('commands/init/docs.mdx', 'command')).toBe('init');
      expect(fileDiscovery.extractName('services/template/docs.md', 'service')).toBe('template');
      expect(fileDiscovery.extractName('guides/setup.mdx', 'guide')).toBe('setup');
    });
  });
});

describe('FrontmatterProcessor Contract Tests', () => {
  let processor: IFrontmatterProcessor;

  beforeEach(() => {
    // This will fail until implementation exists
    // processor = new FrontmatterProcessor();
  });

  describe('Frontmatter Parsing', () => {
    it('should parse valid frontmatter', () => {
      const content = `---
title: Test Command
description: A test command
---

# Content here`;

      const frontmatter = processor.parse(content);
      expect(frontmatter).toEqual({
        title: 'Test Command',
        description: 'A test command'
      });
    });

    it('should return null for missing frontmatter', () => {
      const content = '# Just markdown content';
      expect(processor.parse(content)).toBeNull();
    });
  });

  describe('Frontmatter Injection', () => {
    it('should inject frontmatter into content without frontmatter', () => {
      const content = '# My Content';
      const frontmatter = {
        title: 'My Title',
        description: 'My description'
      };

      const result = processor.inject(content, frontmatter);
      expect(result).toContain('---');
      expect(result).toContain('title: My Title');
      expect(result).toContain('# My Content');
    });

    it('should replace existing frontmatter', () => {
      const content = `---
title: Old Title
---
# Content`;

      const frontmatter = {
        title: 'New Title',
        description: 'New description'
      };

      const result = processor.inject(content, frontmatter);
      expect(result).toContain('title: New Title');
      expect(result).not.toContain('title: Old Title');
    });
  });

  describe('Frontmatter Generation', () => {
    it('should generate default frontmatter for commands', () => {
      const frontmatter = processor.generateDefault('init', 'command');
      
      expect(frontmatter.title).toBe('init');
      expect(frontmatter.description).toContain('init');
      expect(frontmatter.sidebar_label).toBeDefined();
    });
  });

  describe('Frontmatter Validation', () => {
    it('should validate required fields', () => {
      const invalid = { title: '', description: 'Test' };
      const errors = processor.validate(invalid as any);
      
      expect(errors.length).toBeGreaterThan(0);
      expect(errors.some(e => e.includes('title'))).toBe(true);
    });

    it('should pass valid frontmatter', () => {
      const valid = {
        title: 'Valid Title',
        description: 'Valid description'
      };
      
      expect(processor.validate(valid)).toEqual([]);
    });
  });
});

describe('PathMapper Contract Tests', () => {
  let mapper: IPathMapper;

  beforeEach(() => {
    // This will fail until implementation exists
    // mapper = new PathMapper();
  });

  describe('Path Mapping', () => {
    it('should map command paths correctly', () => {
      const source = 'src/specify_cli/commands/init/docs.mdx';
      const dest = mapper.mapPath(source, 'command', 'docs/docs');
      
      expect(dest).toBe('docs/docs/reference/cli/init.mdx');
    });

    it('should map service paths correctly', () => {
      const source = 'src/specify_cli/services/template/docs.md';
      const dest = mapper.mapPath(source, 'service', 'docs/docs');
      
      expect(dest).toBe('docs/docs/reference/api/template.md');
    });

    it('should map guide paths correctly', () => {
      const source = 'src/specify_cli/guides/getting-started.mdx';
      const dest = mapper.mapPath(source, 'guide', 'docs/docs');
      
      expect(dest).toBe('docs/docs/guides/getting-started.mdx');
    });
  });

  describe('Output Directories', () => {
    it('should return correct output subdirectories', () => {
      expect(mapper.getOutputSubdir('command')).toBe('reference/cli');
      expect(mapper.getOutputSubdir('service')).toBe('reference/api');
      expect(mapper.getOutputSubdir('guide')).toBe('guides');
    });

    it('should ensure directory exists', async () => {
      await expect(mapper.ensureDirectory('docs/docs/reference/cli')).resolves.not.toThrow();
    });
  });
});