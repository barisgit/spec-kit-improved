import { join, basename, dirname, extname } from 'path';
import { mkdir } from 'fs/promises';
import type { DocumentationType } from './types';

export class PathMapper {
  private typeToSubdir: Record<DocumentationType, string> = {
    command: 'docs/reference/cli',
    service: 'docs/reference/api',
    guide: 'docs/guides'
  };
  
  /**
   * Map source path to destination path
   */
  mapPath(sourcePath: string, type: DocumentationType, outputDir: string): string {
    const name = this.extractNameFromPath(sourcePath, type);
    const extension = extname(sourcePath);
    const subdir = this.getOutputSubdir(type);
    
    return join(outputDir, subdir, `${name}${extension}`);
  }
  
  /**
   * Get output subdirectory for a documentation type
   */
  getOutputSubdir(type: DocumentationType): string {
    const subdir = this.typeToSubdir[type];
    
    if (!subdir) {
      throw new Error(`Unknown documentation type: ${type}`);
    }
    
    return subdir;
  }
  
  /**
   * Ensure a directory exists, creating it if necessary
   */
  async ensureDirectory(dirPath: string): Promise<void> {
    try {
      await mkdir(dirPath, { recursive: true });
    } catch (error) {
      // Directory might already exist, which is fine
      if ((error as any).code !== 'EEXIST') {
        throw error;
      }
    }
  }
  
  /**
   * Extract name from file path based on type
   */
  extractNameFromPath(filePath: string, type: DocumentationType): string {
    const dir = dirname(filePath);
    const file = basename(filePath);
    
    switch (type) {
      case 'command':
      case 'service':
        // For commands and services, use parent directory name
        return basename(dir);
        
      case 'guide':
        // For guides, use filename without extension
        return basename(file, extname(file));
        
      default:
        return basename(file, extname(file));
    }
  }
}