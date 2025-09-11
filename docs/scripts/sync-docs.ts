#!/usr/bin/env tsx

import { SyncService } from './lib/sync-service';
import { DEFAULT_CONFIG } from './lib/config';
import type { SyncConfiguration } from './lib/types';
import { resolve } from 'path';

/**
 * Main entry point for documentation synchronization
 * Usage: tsx sync-docs.ts [sync|watch|clean]
 */
async function main() {
  const command = process.argv[2] || 'sync';
  
  console.log(`SpecifyX Documentation Sync - ${command} mode`);
  
  const config: SyncConfiguration = {
    ...DEFAULT_CONFIG,
    outputDir: resolve(__dirname, '..'),  // Output to docs/ directory directly
    watch: command === 'watch'  // Enable watch mode when watch command is used
  };
  
  const syncService = new SyncService();
  
  try {
    await syncService.initialize(config);
    
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
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});

export { main };