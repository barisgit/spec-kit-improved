import { EventEmitter } from 'events';
import { watch as chokidarWatch, FSWatcher } from 'chokidar';
import { resolve, dirname } from 'path';
import { glob } from 'glob';
import type {
  SyncConfiguration,
  SyncResult,
  DocumentationFile,
  SyncError,
  SyncEventType
} from './types';
import { FileDiscovery } from './file-discovery';
import { FrontmatterProcessor } from './frontmatter-processor';
import { PathMapper } from './path-mapper';
import { FileOperations } from './file-operations';

export class SyncService extends EventEmitter {
  private config?: SyncConfiguration;
  private fileDiscovery: FileDiscovery;
  private frontmatterProcessor: FrontmatterProcessor;
  private pathMapper: PathMapper;
  private fileOps: FileOperations;
  private watcher?: FSWatcher;
  private filesCache: Map<string, string> = new Map();
  
  constructor() {
    super();
    this.fileDiscovery = new FileDiscovery();
    this.frontmatterProcessor = new FrontmatterProcessor();
    this.fileOps = new FileOperations();
  }
  
  /**
   * Initialize the service with configuration
   */
  async initialize(config: SyncConfiguration): Promise<void> {
    // Initialize PathMapper with the patterns from config
    this.pathMapper = new PathMapper(config.sourcePatterns);
    // Validate configuration
    if (!config.outputDir) {
      throw new Error('Output directory is required');
    }
    
    if (!config.sourcePatterns || config.sourcePatterns.length === 0) {
      throw new Error('At least one source pattern is required');
    }
    
    this.config = config;
    
    // Ensure output directory exists
    await this.pathMapper.ensureDirectory(config.outputDir);
  }
  
  /**
   * Perform a one-time synchronization
   */
  async sync(): Promise<SyncResult> {
    if (!this.config) {
      throw new Error('Service not initialized');
    }
    
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
      // Discover all source files
      const sourceFiles = await this.fileDiscovery.discoverFiles(this.config.sourcePatterns);
      
      // Process each file
      for (const sourcePath of sourceFiles) {
        try {
          const docFile = await this.processFile(sourcePath);
          if (docFile) {
            result.filesProcessed++;
            
            // Check if file is new or updated
            const cached = this.filesCache.get(sourcePath);
            if (!cached) {
              result.filesAdded.push(docFile);
            } else if (cached !== docFile.checksum) {
              result.filesUpdated.push(docFile);
            }
            
            this.filesCache.set(sourcePath, docFile.checksum);
          }
        } catch (error) {
          result.errors.push({
            file: sourcePath,
            error: error instanceof Error ? error.message : String(error),
            type: 'unknown',
            recoverable: true
          });
        }
      }
      
      // Clean orphaned files if configured
      if (this.config.clean) {
        const removed = await this.cleanOrphaned(sourceFiles);
        result.filesRemoved = removed;
      }
      
      this.emit('complete', result);
    } catch (error) {
      this.emit('error', error);
      throw error;
    } finally {
      result.duration = Date.now() - startTime;
    }
    
    return result;
  }
  
  /**
   * Start watching for changes
   */
  async watch(): Promise<void> {
    if (!this.config) {
      throw new Error('Service not initialized');
    }
    
    if (!this.config.watch) {
      throw new Error('Watch mode not enabled in configuration');
    }
    
    // Perform initial sync
    await this.sync();
    
    // Set up file watcher - expand glob patterns first
    const patterns: string[] = [];
    for (const pattern of this.config.sourcePatterns) {
      const fullPattern = resolve(__dirname, '../../..', pattern.pattern);
      const expandedFiles = await glob(fullPattern);
      patterns.push(...expandedFiles);
    }
    
    this.watcher = chokidarWatch(patterns, {
      persistent: true,
      ignoreInitial: true
    });
    
    this.watcher
      .on('add', async (path) => {
        console.log(`File added: ${path}`);
        await this.handleFileChange(path, 'file-added');
      })
      .on('change', async (path) => {
        console.log(`File changed: ${path}`);
        await this.handleFileChange(path, 'file-updated');
      })
      .on('unlink', async (path) => {
        console.log(`File removed: ${path}`);
        await this.handleFileRemoval(path);
      });
  }
  
  /**
   * Stop watching for changes
   */
  async stopWatching(): Promise<void> {
    if (this.watcher) {
      await this.watcher.close();
      this.watcher = undefined;
    }
  }
  
  /**
   * Clean orphaned documentation files
   */
  async clean(): Promise<string[]> {
    if (!this.config) {
      throw new Error('Service not initialized');
    }
    
    const sourceFiles = await this.fileDiscovery.discoverFiles(this.config.sourcePatterns);
    return this.cleanOrphaned(sourceFiles);
  }
  
  /**
   * Validate all documentation files
   */
  async validate(): Promise<SyncError[]> {
    if (!this.config) {
      throw new Error('Service not initialized');
    }
    
    const errors: SyncError[] = [];
    const sourceFiles = await this.fileDiscovery.discoverFiles(this.config.sourcePatterns);
    
    for (const sourcePath of sourceFiles) {
      try {
        const content = await this.fileOps.readFile(sourcePath);
        const frontmatter = this.frontmatterProcessor.parse(content);
        
        if (frontmatter) {
          const validationErrors = this.frontmatterProcessor.validate(frontmatter);
          if (validationErrors.length > 0) {
            errors.push({
              file: sourcePath,
              error: validationErrors.join('; '),
              type: 'validate',
              recoverable: true
            });
          }
        }
      } catch (error) {
        errors.push({
          file: sourcePath,
          error: error instanceof Error ? error.message : String(error),
          type: 'parse',
          recoverable: true
        });
      }
    }
    
    return errors;
  }
  
  /**
   * Process a single documentation file
   */
  private async processFile(sourcePath: string): Promise<DocumentationFile | null> {
    if (!this.config) return null;
    
    // Determine file type
    const type = this.fileDiscovery.getFileType(sourcePath, this.config.sourcePatterns);
    if (!type) return null;
    
    // Read file content
    const content = await this.fileOps.readFile(sourcePath);
    
    // Parse or generate frontmatter
    let frontmatter = this.frontmatterProcessor.parse(content);
    if (!frontmatter) {
      const name = this.fileDiscovery.extractName(sourcePath, type);
      frontmatter = this.frontmatterProcessor.generateDefault(name, type);
    }
    
    // Validate frontmatter if configured
    if (this.config.validate) {
      const errors = this.frontmatterProcessor.validate(frontmatter);
      if (errors.length > 0) {
        console.warn(`Validation errors for ${sourcePath}:`, errors);
      }
    }
    
    // Inject frontmatter if needed
    const processedContent = this.frontmatterProcessor.inject(content, frontmatter);
    
    // Determine destination path
    const destPath = this.pathMapper.mapPath(sourcePath, type, this.config.outputDir);
    
    // Ensure destination directory exists
    await this.pathMapper.ensureDirectory(dirname(destPath));
    
    // Write file
    await this.fileOps.writeFile(destPath, processedContent);
    
    // Create documentation file record
    const docFile: DocumentationFile = {
      sourcePath,
      destPath,
      type,
      name: this.fileDiscovery.extractName(sourcePath, type),
      frontmatter,
      content: processedContent,
      lastModified: await this.fileOps.getModificationTime(sourcePath),
      checksum: this.fileOps.getChecksum(processedContent)
    };
    
    return docFile;
  }
  
  /**
   * Handle file change event
   */
  private async handleFileChange(path: string, eventType: SyncEventType): Promise<void> {
    try {
      const docFile = await this.processFile(path);
      if (docFile) {
        this.filesCache.set(path, docFile.checksum);
        this.emit(eventType, docFile);
      }
    } catch (error) {
      this.emit('error', {
        file: path,
        error: error instanceof Error ? error.message : String(error),
        type: 'unknown',
        recoverable: true
      });
    }
  }
  
  /**
   * Handle file removal event
   */
  private async handleFileRemoval(path: string): Promise<void> {
    if (!this.config) return;
    
    try {
      // Determine destination path
      const type = this.fileDiscovery.getFileType(path, this.config.sourcePatterns);
      if (type) {
        const destPath = this.pathMapper.mapPath(path, type, this.config.outputDir);
        await this.fileOps.deleteFile(destPath);
        this.filesCache.delete(path);
        this.emit('file-removed', destPath);
      }
    } catch (error) {
      this.emit('error', {
        file: path,
        error: error instanceof Error ? error.message : String(error),
        type: 'unknown',
        recoverable: true
      });
    }
  }
  
  /**
   * Clean orphaned files in destination
   * Only cleans files in directories managed by sync (reference/, guides/)
   */
  private async cleanOrphaned(sourceFiles: string[]): Promise<string[]> {
    if (!this.config) return [];
    
    const removed: string[] = [];
    
    // Get all expected destination files
    const expectedDests = new Set<string>();
    for (const sourcePath of sourceFiles) {
      const type = this.fileDiscovery.getFileType(sourcePath, this.config.sourcePatterns);
      if (type) {
        const destPath = this.pathMapper.mapPath(sourcePath, type, this.config.outputDir);
        expectedDests.add(destPath);
      }
    }
    
    // Only clean in managed directories to avoid removing manual docs
    const managedDirs = ['reference', 'guides'];
    const existingFiles: string[] = [];
    
    for (const dir of managedDirs) {
      const dirPattern = resolve(this.config.outputDir, dir, '**/*.{md,mdx}');
      const dirFiles = await glob(dirPattern);
      existingFiles.push(...dirFiles);
    }
    
    // Remove files that don't have a source
    for (const existingFile of existingFiles) {
      if (!expectedDests.has(existingFile)) {
        await this.fileOps.deleteFile(existingFile);
        removed.push(existingFile);
      }
    }
    
    return removed;
  }
}