#!/usr/bin/env tsx

import { resolve, join, basename, dirname, extname } from 'path';
import { glob } from 'glob';
import { readFile, writeFile, mkdir, stat } from 'fs/promises';
import { watch as chokidarWatch, FSWatcher } from 'chokidar';
import matter from 'gray-matter';

/**
 * Improved documentation synchronization script
 *
 * Features:
 * - Configurable directly in this file
 * - Smart filename mapping (use folder name instead of docs.mdx)
 * - Support for single files and patterns
 * - Extensible configuration
 * - No unnecessary type classifications
 */

interface SyncPattern {
  /** Source pattern (glob) */
  source: string;
  /** Output subdirectory relative to docs/ */
  outputDir: string;
  /** Naming strategy */
  naming: 'folder' | 'filename' | 'custom' | 'index';
  /** Custom naming function (if naming: 'custom') */
  customNaming?: (sourcePath: string) => string;
}

interface SyncConfig {
  patterns: SyncPattern[];
  outputBase: string;
  projectRoot: string;
  watch: boolean;
  clean: boolean;
  validate: boolean;
}

// Configuration - edit this directly in the script
const SYNC_CONFIG: SyncConfig = {
  patterns: [
    // CLI commands - use folder name (e.g., init.mdx, check.mdx)
    {
      source: 'src/specify_cli/commands/*/docs.{md,mdx}',
      outputDir: 'docs/reference/cli',
      naming: 'folder'
    },

    // Services - use folder name (e.g., template_service.mdx)
    {
      source: 'src/specify_cli/services/*/docs.{md,mdx}',
      outputDir: 'docs/reference/api',
      naming: 'folder'
    },

    // All assistant-related docs go to assistants section
    {
      source: 'src/specify_cli/assistants/*/docs.{md,mdx}',
      outputDir: 'docs/reference/assistants',
      naming: 'folder'
    },

    // Main assistants overview - becomes index.mdx
    {
      source: 'src/specify_cli/assistants/docs.{md,mdx}',
      outputDir: 'docs/reference/assistants',
      naming: 'custom',
      customNaming: () => 'index'
    },

    // Single files - use filename
    {
      source: 'src/specify_cli/guides/*.{md,mdx}',
      outputDir: 'docs/guides',
      naming: 'filename'
    },

    {
      source: 'src/specify_cli/about/*.{md,mdx}',
      outputDir: 'docs/about',
      naming: 'filename'
    },

    {
      source: 'src/specify_cli/contributing/*.{md,mdx}',
      outputDir: 'docs/contributing',
      naming: 'filename'
    },

    {
      source: 'architecture/**/*.mdx',
      outputDir: 'docs/architecture',
      naming: 'filename'
    }
  ],
  outputBase: resolve(__dirname, '..'),
  projectRoot: resolve(__dirname, '../..'),
  watch: false,
  clean: true,
  validate: true
};

interface ProcessedFile {
  sourcePath: string;
  destPath: string;
  name: string;
  content: string;
  frontmatter: any;
  checksum: string;
}

interface SyncResult {
  filesProcessed: number;
  filesAdded: string[];
  filesUpdated: string[];
  filesRemoved: string[];
  errors: Array<{ file: string; error: string }>;
  duration: number;
}

class DocumentationSync {
  private config: SyncConfig;
  private watcher?: FSWatcher;
  private processedFiles = new Map<string, string>(); // sourcePath -> checksum

  constructor(config: SyncConfig) {
    this.config = config;
  }

  /**
   * Generate destination filename based on naming strategy
   */
  private getDestinationName(sourcePath: string, pattern: SyncPattern): string {
    const ext = extname(sourcePath);

    switch (pattern.naming) {
      case 'folder':
        // Use parent directory name (e.g., claude/docs.mdx -> claude.mdx)
        return basename(dirname(sourcePath)) + ext;

      case 'filename':
        // Use original filename (e.g., quickstart.mdx -> quickstart.mdx)
        return basename(sourcePath);

      case 'custom':
        // Use custom naming function
        if (!pattern.customNaming) {
          throw new Error(`Custom naming function required for pattern: ${pattern.source}`);
        }
        return pattern.customNaming(sourcePath) + ext;

      case 'index':
        // Create index.mdx in a subfolder named after the parent directory
        // e.g., claude/docs.mdx -> claude/index.mdx
        return join(basename(dirname(sourcePath)), 'index' + ext);

      default:
        throw new Error(`Unknown naming strategy: ${pattern.naming}`);
    }
  }

  /**
   * Generate checksum for file content
   */
  private generateChecksum(content: string): string {
    const crypto = require('crypto');
    return crypto.createHash('md5').update(content).digest('hex');
  }

  /**
   * Validate frontmatter
   */
  private validateFrontmatter(frontmatter: any): string[] {
    const errors: string[] = [];

    if (!frontmatter.title || frontmatter.title.trim() === '') {
      errors.push('title is required and cannot be empty');
    }

    if (!frontmatter.description || frontmatter.description.trim() === '') {
      errors.push('description is required and cannot be empty');
    }

    return errors;
  }

  /**
   * Process a single file
   */
  private async processFile(sourcePath: string, pattern: SyncPattern): Promise<ProcessedFile | null> {
    try {
      const content = await readFile(sourcePath, 'utf-8');
      const { data: frontmatter } = matter(content);

      // Validate frontmatter if enabled
      if (this.config.validate) {
        const errors = this.validateFrontmatter(frontmatter);
        if (errors.length > 0) {
          console.log(`Validation errors for ${sourcePath}:`, errors);
          return null;
        }
      }

      const destName = this.getDestinationName(sourcePath, pattern);
      const destPath = join(this.config.outputBase, pattern.outputDir, destName);
      const checksum = this.generateChecksum(content);

      // Ensure output directory exists
      await mkdir(dirname(destPath), { recursive: true });

      return {
        sourcePath,
        destPath,
        name: destName,
        content,
        frontmatter,
        checksum
      };

    } catch (error) {
      throw new Error(`Failed to process ${sourcePath}: ${error instanceof Error ? error.message : error}`);
    }
  }

  /**
   * Discover files for all patterns
   */
  private async discoverFiles(): Promise<Array<{ file: string; pattern: SyncPattern }>> {
    const results: Array<{ file: string; pattern: SyncPattern }> = [];

    for (const pattern of this.config.patterns) {
      try {
        const files = await glob(pattern.source, {
          cwd: this.config.projectRoot,
          absolute: true
        });

        for (const file of files) {
          results.push({ file, pattern });
        }
      } catch (error) {
        console.error(`Error discovering files for pattern ${pattern.source}:`, error);
      }
    }

    return results;
  }

  /**
   * Perform synchronization
   */
  async sync(): Promise<SyncResult> {
    const startTime = Date.now();
    const result: SyncResult = {
      filesProcessed: 0,
      filesAdded: [],
      filesUpdated: [],
      filesRemoved: [],
      errors: [],
      duration: 0
    };

    try {
      const discovered = await this.discoverFiles();

      for (const { file, pattern } of discovered) {
        try {
          const processed = await this.processFile(file, pattern);
          if (processed) {
            result.filesProcessed++;

            // Check if file exists and has changed
            let fileExists = false;
            try {
              await stat(processed.destPath);
              fileExists = true;
            } catch {
              // File doesn't exist
            }

            const previousChecksum = this.processedFiles.get(processed.sourcePath);
            const hasChanged = previousChecksum !== processed.checksum;

            if (!fileExists || hasChanged) {
              await writeFile(processed.destPath, processed.content, 'utf-8');

              if (!fileExists) {
                result.filesAdded.push(processed.destPath);
              } else {
                result.filesUpdated.push(processed.destPath);
              }
            }

            this.processedFiles.set(processed.sourcePath, processed.checksum);
          }
        } catch (error) {
          result.errors.push({
            file,
            error: error instanceof Error ? error.message : String(error)
          });
        }
      }

    } catch (error) {
      result.errors.push({
        file: 'global',
        error: error instanceof Error ? error.message : String(error)
      });
    }

    result.duration = Date.now() - startTime;
    return result;
  }

  /**
   * Start watching for changes
   */
  async watch(): Promise<void> {
    if (this.watcher) {
      return;
    }

    const patterns = this.config.patterns.map(p => p.source);

    this.watcher = chokidarWatch(patterns, {
      persistent: true,
      ignoreInitial: false
    });

    this.watcher.on('ready', () => {
      console.log('Initial scan complete. Ready for changes');
    });

    this.watcher.on('add', async (path) => {
      console.log(`File added: ${path}`);
      await this.syncSingle(path);
    });

    this.watcher.on('change', async (path) => {
      console.log(`File changed: ${path}`);
      await this.syncSingle(path);
    });

    this.watcher.on('unlink', async (path) => {
      console.log(`File removed: ${path}`);
      // TODO: Remove corresponding output file
    });
  }

  /**
   * Sync a single file
   */
  private async syncSingle(sourcePath: string): Promise<void> {
    for (const pattern of this.config.patterns) {
      const files = await glob(pattern.source, { cwd: this.config.projectRoot, absolute: true });
      if (files.includes(sourcePath)) {
        try {
          const processed = await this.processFile(sourcePath, pattern);
          if (processed) {
            await writeFile(processed.destPath, processed.content, 'utf-8');
            this.processedFiles.set(processed.sourcePath, processed.checksum);
            console.log(`Synced: ${basename(processed.destPath)}`);
          }
        } catch (error) {
          console.error(`Error syncing ${sourcePath}:`, error);
        }
        break;
      }
    }
  }

  /**
   * Stop watching
   */
  async stopWatching(): Promise<void> {
    if (this.watcher) {
      await this.watcher.close();
      this.watcher = undefined;
    }
  }

  /**
   * Clean orphaned files (TODO: implement)
   */
  async clean(): Promise<string[]> {
    // TODO: Implement cleaning of orphaned files
    return [];
  }
}

/**
 * Main entry point
 */
async function main() {
  const command = process.argv[2] || 'sync';

  console.log(`SpecifyX Documentation Sync - ${command} mode`);

  const config: SyncConfig = {
    ...SYNC_CONFIG,
    watch: command === 'watch',
    projectRoot: resolve(__dirname, '../..')
  };

  const syncService = new DocumentationSync(config);

  try {
    switch (command) {
      case 'watch':
        console.log('Watching for documentation changes...');
        await syncService.watch();

        // Keep process running
        process.on('SIGINT', async () => {
          console.log('\nStopping watch mode...');
          await syncService.stopWatching();
          process.exit(0);
        });
        break;

      case 'clean':
        console.log('Cleaning orphaned documentation files...');
        const removed = await syncService.clean();
        console.log(`Removed ${removed.length} orphaned files`);
        if (removed.length > 0) {
          removed.forEach(file => console.log(`  - ${file}`));
        }
        break;

      case 'sync':
      default: {
        console.log('Syncing documentation...');
        const result = await syncService.sync();

        console.log(`Sync completed in ${result.duration}ms`);
        console.log(`  Files processed: ${result.filesProcessed}`);
        console.log(`  Added: ${result.filesAdded.length}`);
        console.log(`  Updated: ${result.filesUpdated.length}`);
        console.log(`  Removed: ${result.filesRemoved.length}`);

        if (result.errors.length > 0) {
          console.log(`  Errors: ${result.errors.length}`);
          result.errors.forEach(error => {
            console.log(`    - ${error.file}: ${error.error}`);
          });
        }
        break;
      }
    }
  } catch (error) {
    console.error('Error:', error instanceof Error ? error.message : error);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export { main };
