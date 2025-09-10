import { readFile, writeFile, unlink, stat } from 'fs/promises';
import { createHash } from 'crypto';

export class FileOperations {
  /**
   * Read file content
   */
  async readFile(filePath: string): Promise<string> {
    try {
      const content = await readFile(filePath, 'utf-8');
      return content;
    } catch (error) {
      throw new Error(`Failed to read file ${filePath}: ${error}`);
    }
  }
  
  /**
   * Write file content
   */
  async writeFile(filePath: string, content: string): Promise<void> {
    try {
      await writeFile(filePath, content, 'utf-8');
    } catch (error) {
      throw new Error(`Failed to write file ${filePath}: ${error}`);
    }
  }
  
  /**
   * Delete a file
   */
  async deleteFile(filePath: string): Promise<void> {
    try {
      await unlink(filePath);
    } catch (error) {
      // File might not exist, which is okay
      if ((error as any).code !== 'ENOENT') {
        throw new Error(`Failed to delete file ${filePath}: ${error}`);
      }
    }
  }
  
  /**
   * Get file checksum
   */
  getChecksum(content: string): string {
    return createHash('md5').update(content).digest('hex');
  }
  
  /**
   * Get file modification time
   */
  async getModificationTime(filePath: string): Promise<Date> {
    try {
      const stats = await stat(filePath);
      return stats.mtime;
    } catch (error) {
      throw new Error(`Failed to get modification time for ${filePath}: ${error}`);
    }
  }
}