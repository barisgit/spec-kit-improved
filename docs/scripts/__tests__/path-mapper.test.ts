import { describe, it, expect, beforeEach } from 'vitest';
import path from 'path';

// This import will fail until implementation exists
import { PathMapper } from '../lib/path-mapper';

describe('PathMapper', () => {
  let mapper: PathMapper;
  const outputDir = 'docs/src/content/docs';
  
  beforeEach(() => {
    mapper = new PathMapper();
  });

  describe('mapPath', () => {
    it('should map command paths correctly', () => {
      const source = '../src/specify_cli/commands/init/docs.mdx';
      const dest = mapper.mapPath(source, 'command', outputDir);
      
      expect(dest).toBe(path.join(outputDir, 'docs/reference/cli/init.mdx'));
    });

    it('should map service paths correctly', () => {
      const source = '../src/specify_cli/services/template_service/docs.md';
      const dest = mapper.mapPath(source, 'service', outputDir);
      
      expect(dest).toBe(path.join(outputDir, 'docs/reference/api/template_service.md'));
    });

    it('should map assistant paths correctly', () => {
        const source = '../src/specify_cli/assistants/claude/docs.mdx';
        const dest = mapper.mapPath(source, 'assistant', outputDir);

        expect(dest).toBe(path.join(outputDir, 'docs/reference/assistants/claude.mdx'));
    });

    it('should map guide paths correctly', () => {
      const source = '../src/specify_cli/guides/getting-started.mdx';
      const dest = mapper.mapPath(source, 'guide', outputDir);
      
      expect(dest).toBe(path.join(outputDir, 'docs/guides/getting-started.mdx'));
    });

    it('should map architecture paths correctly', () => {
      const source = '../architecture/system-overview.mdx';
      const dest = mapper.mapPath(source, 'architecture', outputDir);

      expect(dest).toBe(path.join(outputDir, 'docs/architecture/system-overview.mdx'));
    });

    it('should preserve file extensions', () => {
      const sourceMd = '../src/specify_cli/commands/test/docs.md';
      const sourceMdx = '../src/specify_cli/commands/test/docs.mdx';
      
      const destMd = mapper.mapPath(sourceMd, 'command', outputDir);
      const destMdx = mapper.mapPath(sourceMdx, 'command', outputDir);
      
      expect(destMd).toContain('.md');
      expect(destMd).not.toContain('.mdx');
      expect(destMdx).toContain('.mdx');
    });

    it('should handle nested command directories', () => {
      const source = '../src/specify_cli/commands/subcommand/nested/docs.mdx';
      const dest = mapper.mapPath(source, 'command', outputDir);
      
      // Should extract the immediate parent directory name
      expect(dest).toBe(path.join(outputDir, 'docs/reference/cli/nested.mdx'));
    });
  });

  describe('getOutputSubdir', () => {
    it('should return correct output subdirectory for commands', () => {
      expect(mapper.getOutputSubdir('command')).toBe('docs/reference/cli');
    });

    it('should return correct output subdirectory for services', () => {
      expect(mapper.getOutputSubdir('service')).toBe('docs/reference/api');
    });

    it('should return correct output subdirectory for assistants', () => {
      expect(mapper.getOutputSubdir('assistant')).toBe('docs/reference/assistants');
    });

    it('should return correct output subdirectory for guides', () => {
      expect(mapper.getOutputSubdir('guide')).toBe('docs/guides');
    });

    it('should return correct output subdirectory for architecture', () => {
      expect(mapper.getOutputSubdir('architecture')).toBe('docs/architecture');
    });

    it('should throw for unknown type', () => {
      expect(() => mapper.getOutputSubdir('unknown' as any)).toThrow();
    });
  });

  describe('ensureDirectory', () => {
    it('should create directory if it does not exist', async () => {
      const testDir = path.join(outputDir, 'test-dir');
      await mapper.ensureDirectory(testDir);
      
      // Should not throw
      expect(true).toBe(true);
    });

    it('should not throw if directory already exists', async () => {
      const existingDir = outputDir;
      await mapper.ensureDirectory(existingDir);
      
      // Should not throw
      expect(true).toBe(true);
    });

    it('should create nested directories', async () => {
      const nestedDir = path.join(outputDir, 'deep/nested/path');
      await mapper.ensureDirectory(nestedDir);
      
      // Should not throw
      expect(true).toBe(true);
    });
  });

  describe('extractNameFromPath', () => {
    it('should extract name from command path', () => {
      const name = mapper.extractNameFromPath(
        '../src/specify_cli/commands/init/docs.mdx',
        'command'
      );
      expect(name).toBe('init');
    });

    it('should extract name from service path', () => {
      const name = mapper.extractNameFromPath(
        '../src/specify_cli/services/template_service/docs.md',
        'service'
      );
      expect(name).toBe('template_service');
    });

    it('should extract name from guide path', () => {
      const name = mapper.extractNameFromPath(
        '../src/specify_cli/guides/getting-started.mdx',
        'guide'
      );
      expect(name).toBe('getting-started');
    });

    it('should handle paths without extension', () => {
      const name = mapper.extractNameFromPath(
        '../src/specify_cli/guides/readme',
        'guide'
      );
      expect(name).toBe('readme');
    });
  });
});
