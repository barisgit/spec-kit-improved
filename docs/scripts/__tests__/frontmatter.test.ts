import { describe, it, expect, beforeEach } from 'vitest';
import type { FrontmatterData } from '../lib/types';

// This import will fail until implementation exists
import { FrontmatterProcessor } from '../lib/frontmatter-processor';

describe('FrontmatterProcessor', () => {
  let processor: FrontmatterProcessor;
  
  beforeEach(() => {
    processor = new FrontmatterProcessor();
  });

  describe('parse', () => {
    it('should parse valid frontmatter', () => {
      const content = `---
title: Test Command
description: A test command for documentation
sidebar_label: test
---

# Test Command

This is the content.`;

      const frontmatter = processor.parse(content);
      expect(frontmatter).toEqual({
        title: 'Test Command',
        description: 'A test command for documentation',
        sidebar_label: 'test'
      });
    });

    it('should return null for missing frontmatter', () => {
      const content = '# Just Markdown\n\nNo frontmatter here.';
      const frontmatter = processor.parse(content);
      expect(frontmatter).toBeNull();
    });

    it('should handle empty frontmatter', () => {
      const content = `---
---

# Content`;
      
      const frontmatter = processor.parse(content);
      expect(frontmatter).toEqual({});
    });

    it('should parse frontmatter with arrays', () => {
      const content = `---
title: Test
keywords:
  - cli
  - documentation
  - testing
---

Content`;

      const frontmatter = processor.parse(content);
      expect(frontmatter?.keywords).toEqual(['cli', 'documentation', 'testing']);
    });
  });

  describe('inject', () => {
    it('should inject frontmatter into content without frontmatter', () => {
      const content = '# My Documentation\n\nSome content here.';
      const frontmatter: FrontmatterData = {
        title: 'My Title',
        description: 'My description'
      };

      const result = processor.inject(content, frontmatter);
      expect(result).toContain('---');
      expect(result).toContain('title: My Title');
      expect(result).toContain('description: My description');
      expect(result).toContain('# My Documentation');
    });

    it('should replace existing frontmatter', () => {
      const content = `---
title: Old Title
---

# Content`;

      const frontmatter: FrontmatterData = {
        title: 'New Title',
        description: 'New description'
      };

      const result = processor.inject(content, frontmatter);
      expect(result).toContain('title: New Title');
      expect(result).toContain('description: New description');
      expect(result).not.toContain('Old Title');
    });

    it('should preserve content after frontmatter', () => {
      const content = '# Header\n\n## Subheader\n\nParagraph text.';
      const frontmatter: FrontmatterData = {
        title: 'Test'
      };

      const result = processor.inject(content, frontmatter);
      expect(result).toContain('# Header');
      expect(result).toContain('## Subheader');
      expect(result).toContain('Paragraph text.');
    });
  });

  describe('generateDefault', () => {
    it('should generate default frontmatter for commands', () => {
      const frontmatter = processor.generateDefault('init', 'command');
      
      expect(frontmatter.title).toBe('Init');
      expect(frontmatter.description).toContain('init');
      expect(frontmatter.sidebar_label).toBe('init');
    });

    it('should generate default frontmatter for services', () => {
      const frontmatter = processor.generateDefault('template_service', 'service');
      
      expect(frontmatter.title).toBe('Template Service');
      expect(frontmatter.description).toContain('template_service');
    });

    it('should generate default frontmatter for guides', () => {
      const frontmatter = processor.generateDefault('getting-started', 'guide');
      
      expect(frontmatter.title).toBeTruthy();
      expect(frontmatter.description).toBeTruthy();
    });

    it('should handle hyphenated names', () => {
      const frontmatter = processor.generateDefault('my-awesome-feature', 'command');
      
      expect(frontmatter.title).toContain('My Awesome Feature');
    });
  });

  describe('validate', () => {
    it('should validate required fields', () => {
      const invalid: FrontmatterData = {
        title: '',
        description: 'Test'
      };
      
      const errors = processor.validate(invalid);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors.some(e => e.includes('title'))).toBe(true);
    });

    it('should pass valid frontmatter', () => {
      const valid: FrontmatterData = {
        title: 'Valid Title',
        description: 'Valid description'
      };
      
      const errors = processor.validate(valid);
      expect(errors).toEqual([]);
    });

    it('should validate description length', () => {
      const tooLong: FrontmatterData = {
        title: 'Title',
        description: 'a'.repeat(200)
      };
      
      const errors = processor.validate(tooLong);
      expect(errors.some(e => e.includes('description'))).toBe(true);
    });
  });
});