#!/usr/bin/env tsx

import { watch } from 'chokidar';
import { exec } from 'child_process';
import { promisify } from 'util';
import chalk from 'chalk';
import { resolve } from 'path';

const execAsync = promisify(exec);

class GenerationWatcher {
  private isGenerating = false;
  private pendingRegeneration = false;
  private isReady = false;

  /**
   * Regenerate documentation by running the generate command
   */
  private async regenerateDocumentation(): Promise<void> {
    if (this.isGenerating) {
      this.pendingRegeneration = true;
      return;
    }

    this.isGenerating = true;
    console.log(chalk.hex('#FFA500')('\nRegenerating documentation...'));

    try {
      const { stderr } = await execAsync('pnpm run generate');

      if (stderr && !stderr.includes('warn')) {
        console.error(chalk.red('Error during generation:'), stderr);
      } else {
        console.log(chalk.green('Documentation regenerated successfully'));
      }
    } catch (error) {
      console.error(chalk.red('Failed to regenerate documentation:'), error);
    } finally {
      this.isGenerating = false;

      // If there was a pending regeneration request, run it now
      if (this.pendingRegeneration) {
        this.pendingRegeneration = false;
        setTimeout(() => this.regenerateDocumentation(), 100);
      }
    }
  }

  /**
   * Start watching Python source files for changes
   */
  public async startWatching(): Promise<void> {
    console.log(chalk.cyan('Starting documentation generation watch mode...'));

    // Set up project root and watch pattern
    const projectRoot = resolve(__dirname, '../..');
    const watchPattern = 'src/specify_cli/**/*.py';

    // Discover files first using glob
    let filesToWatch: string[] = [];
    try {
      const { glob } = await import('glob');
      filesToWatch = await glob(watchPattern, { cwd: projectRoot, absolute: true });

      if (filesToWatch.length === 0) {
        console.error(chalk.red('No Python files found!'));
        return;
      }

      console.log(chalk.gray(`Watching ${filesToWatch.length} Python files for changes...`));
    } catch (error) {
      console.error(chalk.red('Error discovering files:'), error);
      return;
    }

    // Create watcher using discovered file paths (like sync-docs.ts approach)
    const watcher = watch(filesToWatch, {
      ignored: [
        '**/.*',               // Ignore hidden files
        '**/__pycache__/**',   // Ignore Python cache
        '**/tests/**',         // Ignore test files
        '**/*.pyc',            // Ignore compiled Python files
        '**/test_*.py',        // Ignore test files
        '**/*_test.py'         // Ignore test files
      ],
      persistent: true,
      ignoreInitial: false,  // Enable to see what files are found initially
      awaitWriteFinish: {     // Wait for file writes to complete
        stabilityThreshold: 300,
        pollInterval: 100
      }
    });

    // Set up event handlers
    watcher
      .on('change', (path) => {
        console.log(chalk.blue(`Changed: ${path.replace(projectRoot, '.')}`));
        this.regenerateDocumentation();
      })
      .on('add', (path) => {
        // Only regenerate on actual new files after ready
        if (this.isReady) {
          console.log(chalk.green(`Added: ${path.replace(projectRoot, '.')}`));
          this.regenerateDocumentation();
        }
      })
      .on('unlink', (path) => {
        console.log(chalk.yellow(`Removed: ${path.replace(projectRoot, '.')}`));
        this.regenerateDocumentation();
      })
      .on('error', (error) => {
        console.error(chalk.red('Watcher error:'), error);
      })
      .on('ready', () => {
        console.log(chalk.cyan('Ready. Watching for changes... (Press Ctrl+C to stop)\n'));
        this.isReady = true;
      });

    // Graceful shutdown
    process.on('SIGINT', () => {
      console.log(chalk.yellow('\nStopping documentation watcher...'));
      watcher.close();
      process.exit(0);
    });

    process.on('SIGTERM', () => {
      console.log(chalk.yellow('\nStopping documentation watcher...'));
      watcher.close();
      process.exit(0);
    });

    // Initial generation
    await this.regenerateDocumentation();
  }
}

// Start the watcher
const watcher = new GenerationWatcher();
watcher.startWatching().catch((error) => {
  console.error(chalk.red('Failed to start watcher:'), error);
  process.exit(1);
});