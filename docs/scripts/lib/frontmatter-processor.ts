import matter from 'gray-matter';
import type { FrontmatterData, DocumentationType } from './types';

export class FrontmatterProcessor {
  /**
   * Parse frontmatter from content
   */
  parse(content: string): FrontmatterData | null {
    try {
      const { data, content: bodyContent } = matter(content);
      
      // Return null if no frontmatter found
      if (Object.keys(data).length === 0 && !content.startsWith('---')) {
        return null;
      }
      
      return data as FrontmatterData;
    } catch (error) {
      console.warn('Failed to parse frontmatter:', error);
      return null;
    }
  }
  
  /**
   * Inject frontmatter into content
   */
  inject(content: string, frontmatter: FrontmatterData): string {
    try {
      // Parse existing content to extract body
      const { content: bodyContent } = matter(content);
      
      // Create new content with updated frontmatter
      const newContent = matter.stringify(bodyContent, frontmatter);
      
      return newContent;
    } catch (error) {
      // If parsing fails, just prepend frontmatter
      const frontmatterStr = this.stringifyFrontmatter(frontmatter);
      return `---\n${frontmatterStr}---\n\n${content}`;
    }
  }
  
  /**
   * Generate default frontmatter based on name and type
   */
  generateDefault(name: string, type: DocumentationType): FrontmatterData {
    // Convert hyphenated names to title case
    const title = this.nameToTitle(name);
    
    let description = '';
    switch (type) {
      case 'command':
        description = `Documentation for the ${name} command`;
        break;
      case 'service':
        description = `API documentation for the ${name} service`;
        break;
      case 'assistant':
        description = `${title} assistant reference`;
        break;
      case 'guide':
        description = `${title} guide`;
        break;
      case 'about':
        description = `${title} reference material`;
        break;
      case 'contributing':
        description = `${title} contribution guide`;
        break;
      case 'architecture':
        description = `${title} architecture overview`;
        break;
      default:
        description = `${title}`;
        break;
    }
    
    return {
      title,
      description,
      sidebar_label: name
    };
  }
  
  /**
   * Validate frontmatter data
   */
  validate(frontmatter: FrontmatterData): string[] {
    const errors: string[] = [];
    
    // Check required fields
    if (!frontmatter.title || frontmatter.title.trim() === '') {
      errors.push('title is required and cannot be empty');
    }
    
    if (!frontmatter.description || frontmatter.description.trim() === '') {
      errors.push('description is required and cannot be empty');
    }
    
    // Check description length
    if (frontmatter.description && frontmatter.description.length > 160) {
      errors.push('description should be under 160 characters for SEO');
    }
    
    // Check sidebar_position is valid if present
    if (frontmatter.sidebar_position !== undefined) {
      if (!Number.isInteger(frontmatter.sidebar_position) || frontmatter.sidebar_position < 0) {
        errors.push('sidebar_position must be a positive integer');
      }
    }
    
    return errors;
  }
  
  /**
   * Convert a hyphenated name to title case
   */
  private nameToTitle(name: string): string {
    return name
      .split(/[-_]/)
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }
  
  /**
   * Stringify frontmatter object to YAML
   */
  private stringifyFrontmatter(frontmatter: FrontmatterData): string {
    const lines: string[] = [];
    
    for (const [key, value] of Object.entries(frontmatter)) {
      if (Array.isArray(value)) {
        lines.push(`${key}:`);
        value.forEach(item => lines.push(`  - ${item}`));
      } else if (typeof value === 'object' && value !== null) {
        lines.push(`${key}:`);
        for (const [subKey, subValue] of Object.entries(value)) {
          lines.push(`  ${subKey}: ${subValue}`);
        }
      } else {
        lines.push(`${key}: ${value}`);
      }
    }
    
    return lines.join('\n') + '\n';
  }
}
