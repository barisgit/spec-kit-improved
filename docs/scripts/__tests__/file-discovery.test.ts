import { describe, it, expect, beforeEach } from 'vitest';
import type { PathPattern } from '../lib/types';

// This import will fail until implementation exists
import { FileDiscovery } from '../lib/file-discovery';

describe('FileDiscovery', () => {
  let fileDiscovery: FileDiscovery;
  
  beforeEach(() => {
    fileDiscovery = new FileDiscovery();
  });

  describe('discoverFiles', () => {
    it('should discover command documentation files', async () => {
      const patterns: PathPattern[] = [
        {
          pattern: '../src/specify_cli/commands/*/docs.{md,mdx}',
          type: 'command',
          outputSubdir: 'reference/cli'
        }
      ];
      
      const files = await fileDiscovery.discoverFiles(patterns);
      expect(Array.isArray(files)).toBe(true);
      expect(files.every(f => f.includes('commands'))).toBe(true);
    });

    it('should discover service documentation files', async () => {
      const patterns: PathPattern[] = [
        {
          pattern: '../src/specify_cli/services/*/docs.{md,mdx}',
          type: 'service',
          outputSubdir: 'reference/api'
        }
      ];
      
      const files = await fileDiscovery.discoverFiles(patterns);
      expect(Array.isArray(files)).toBe(true);
    });

    it('should discover assistant documentation files', async () => {
      const patterns: PathPattern[] = [
        {
          pattern: '../src/specify_cli/assistants/*/docs.{md,mdx}',
          type: 'assistant',
          outputSubdir: 'reference/assistants'
        }
      ];

      const files = await fileDiscovery.discoverFiles(patterns);
      expect(Array.isArray(files)).toBe(true);
    });

    it('should discover guide documentation files', async () => {
      const patterns: PathPattern[] = [
        {
          pattern: '../src/specify_cli/guides/*.{md,mdx}',
          type: 'guide',
          outputSubdir: 'guides'
        }
      ];
      
      const files = await fileDiscovery.discoverFiles(patterns);
      expect(Array.isArray(files)).toBe(true);
    });

    it('should handle empty results gracefully', async () => {
      const patterns: PathPattern[] = [
        {
          pattern: 'non/existent/path/*.mdx',
          type: 'command',
          outputSubdir: 'reference/cli'
        }
      ];
      
      const files = await fileDiscovery.discoverFiles(patterns);
      expect(files).toEqual([]);
    });

    it('should discover architecture documentation files', async () => {
      const patterns: PathPattern[] = [
        {
          pattern: '../architecture/*.mdx',
          type: 'architecture',
          outputSubdir: 'architecture'
        }
      ];

      const files = await fileDiscovery.discoverFiles(patterns);
      expect(Array.isArray(files)).toBe(true);
    });
  });

  describe('getFileType', () => {
    const patterns: PathPattern[] = [
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
        pattern: '../src/specify_cli/assistants/*/docs.{md,mdx}',
        type: 'assistant',
        outputSubdir: 'reference/assistants'
      },
      {
        pattern: '../src/specify_cli/guides/*.{md,mdx}',
        type: 'guide',
        outputSubdir: 'guides'
      },
      {
        pattern: '../architecture/*.mdx',
        type: 'architecture',
        outputSubdir: 'architecture'
      }
    ];

    it('should identify command files', () => {
      const type = fileDiscovery.getFileType(
        '../src/specify_cli/commands/init/docs.mdx',
        patterns
      );
      expect(type).toBe('command');
    });

    it('should identify service files', () => {
      const type = fileDiscovery.getFileType(
        '../src/specify_cli/services/template_service/docs.md',
        patterns
      );
      expect(type).toBe('service');
    });

    it('should identify assistant files', () => {
      const type = fileDiscovery.getFileType(
        '../src/specify_cli/assistants/claude/docs.mdx',
        patterns
      );
      expect(type).toBe('assistant');
    });

    it('should identify guide files', () => {
      const type = fileDiscovery.getFileType(
        '../src/specify_cli/guides/getting-started.mdx',
        patterns
      );
      expect(type).toBe('guide');
    });

    it('should identify architecture files', () => {
      const type = fileDiscovery.getFileType(
        '../architecture/system-overview.mdx',
        patterns
      );
      expect(type).toBe('architecture');
    });

    it('should return null for non-matching files', () => {
      const type = fileDiscovery.getFileType(
        'some/random/file.txt',
        patterns
      );
      expect(type).toBeNull();
    });
  });

  describe('extractName', () => {
    it('should extract command name from path', () => {
      const name = fileDiscovery.extractName(
        '../src/specify_cli/commands/init/docs.mdx',
        'command'
      );
      expect(name).toBe('init');
    });

    it('should extract service name from path', () => {
      const name = fileDiscovery.extractName(
        '../src/specify_cli/services/template_service/docs.md',
        'service'
      );
      expect(name).toBe('template_service');
    });

    it('should extract assistant name from path', () => {
      const name = fileDiscovery.extractName(
        '../src/specify_cli/assistants/claude/docs.mdx',
        'assistant'
      );
      expect(name).toBe('claude');
    });

    it('should extract guide name from path', () => {
      const name = fileDiscovery.extractName(
        '../src/specify_cli/guides/getting-started.mdx',
        'guide'
      );
      expect(name).toBe('getting-started');
    });

    it('should extract architecture name from path', () => {
      const name = fileDiscovery.extractName(
        '../architecture/system-overview.mdx',
        'architecture'
      );
      expect(name).toBe('system-overview');
    });
  });
});
