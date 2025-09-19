import { glob } from 'glob';
import { resolve, dirname, basename, extname } from 'path';
import type { PathPattern, DocumentationType } from './types';

export class FileDiscovery {
  /**
   * Discover documentation files based on patterns
   */
  async discoverFiles(patterns: PathPattern[]): Promise<string[]> {
    const allFiles: string[] = [];
    
    for (const pattern of patterns) {
      try {
        // Resolve pattern relative to project root (go up from docs/scripts/lib)
        const fullPattern = resolve(__dirname, '../../../', pattern.pattern);
        const files = await glob(fullPattern, {
          nodir: true,
          absolute: true
        });
        
        // Filter out README files
        const filteredFiles = files.filter(file => !basename(file).toLowerCase().startsWith('readme'));
        allFiles.push(...filteredFiles);
      } catch (error) {
        console.warn(`Failed to process pattern ${pattern.pattern}:`, error);
      }
    }
    
    return allFiles;
  }
  
  /**
   * Get the documentation type for a file based on patterns
   */
  getFileType(filePath: string, patterns: PathPattern[]): DocumentationType | null {
    // Normalize the file path for comparison
    const normalizedPath = filePath.replace(/\\/g, '/');
    
    for (const pattern of patterns) {
      // Convert glob pattern to regex for matching
      const patternRegex = this.globToRegex(pattern.pattern);
      
      if (patternRegex.test(normalizedPath)) {
        return pattern.type;
      }
    }
    
    return null;
  }
  
  /**
   * Extract name from file path based on type
   */
  extractName(filePath: string, type: DocumentationType): string {
    const dir = dirname(filePath);
    const file = basename(filePath);
    
    switch (type) {
      case 'command':
      case 'service':
      case 'assistant':
        // For commands and services, use parent directory name
        return basename(dir);

      case 'guide':
      case 'about':
      case 'contributing':
      case 'architecture':
        // Use filename without extension for content-style docs
        return basename(file, extname(file));

      default:
        return basename(file, extname(file));
    }
  }
  
  /**
   * Convert glob pattern to regex
   */
  private globToRegex(pattern: string): RegExp {
    // Escape special regex characters except glob wildcards
    let regex = pattern
      .replace(/\./g, '\\.')
      .replace(/\//g, '\\/')
      .replace(/\*/g, '[^/]*')
      .replace(/\?/g, '.')
      .replace(/\{([^}]+)\}/g, (match, group) => {
        // Handle {md,mdx} style alternatives
        const alternatives = group.split(',').join('|');
        return `(${alternatives})`;
      });
    
    // Make it match the end of the path
    regex = regex + '$';
    
    return new RegExp(regex);
  }
}
