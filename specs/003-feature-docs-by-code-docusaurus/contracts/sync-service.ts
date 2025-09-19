/**
 * Contract definitions for the documentation synchronization service
 * These interfaces define the expected behavior that must be tested
 */

// ============================================================================
// Core Data Types
// ============================================================================

export type DocumentationType =
  | 'command'
  | 'service'
  | 'assistant'
  | 'guide'
  | 'about'
  | 'contributing'
  | 'architecture';

export interface FrontmatterData {
  title: string;
  description: string;
  sidebar_label?: string;
  sidebar_position?: number;
  keywords?: string[];
  hide_title?: boolean;
}

export interface DocumentationFile {
  sourcePath: string;
  destPath: string;
  type: DocumentationType;
  name: string;
  frontmatter: FrontmatterData;
  content: string;
  lastModified: Date;
  checksum: string;
}

export interface PathPattern {
  pattern: string;
  type: DocumentationType;
  outputSubdir: string;
}

export interface SyncConfiguration {
  sourcePatterns: PathPattern[];
  outputDir: string;
  watch: boolean;
  clean: boolean;
  validate: boolean;
  preserveExtensions: boolean;
}

export interface SyncError {
  file: string;
  error: string;
  type: 'parse' | 'validate' | 'write' | 'unknown';
  recoverable: boolean;
}

export interface SyncResult {
  filesProcessed: number;
  filesAdded: DocumentationFile[];
  filesUpdated: DocumentationFile[];
  filesRemoved: string[];
  errors: SyncError[];
  duration: number;
}

// ============================================================================
// Service Contracts
// ============================================================================

/**
 * Main synchronization service contract
 */
export interface ISyncService {
  /**
   * Initialize the service with configuration
   */
  initialize(config: SyncConfiguration): Promise<void>;

  /**
   * Perform a one-time synchronization
   */
  sync(): Promise<SyncResult>;

  /**
   * Start watching for changes
   */
  watch(): Promise<void>;

  /**
   * Stop watching for changes
   */
  stopWatching(): Promise<void>;

  /**
   * Clean orphaned documentation files
   */
  clean(): Promise<string[]>;

  /**
   * Validate all documentation files
   */
  validate(): Promise<SyncError[]>;
}

/**
 * File discovery service contract
 */
export interface IFileDiscovery {
  /**
   * Discover documentation files based on patterns
   */
  discoverFiles(patterns: PathPattern[]): Promise<string[]>;

  /**
   * Get the documentation type for a file
   */
  getFileType(filePath: string, patterns: PathPattern[]): DocumentationType | null;

  /**
   * Extract name from file path
   */
  extractName(filePath: string, type: DocumentationType): string;
}

/**
 * Frontmatter processing service contract
 */
export interface IFrontmatterProcessor {
  /**
   * Parse frontmatter from content
   */
  parse(content: string): FrontmatterData | null;

  /**
   * Inject frontmatter into content
   */
  inject(content: string, frontmatter: FrontmatterData): string;

  /**
   * Generate default frontmatter
   */
  generateDefault(name: string, type: DocumentationType): FrontmatterData;

  /**
   * Validate frontmatter data
   */
  validate(frontmatter: FrontmatterData): string[];
}

/**
 * Path mapping service contract
 */
export interface IPathMapper {
  /**
   * Map source path to destination path
   */
  mapPath(sourcePath: string, type: DocumentationType, outputDir: string): string;

  /**
   * Get output subdirectory for type
   */
  getOutputSubdir(type: DocumentationType): string;

  /**
   * Ensure destination directory exists
   */
  ensureDirectory(dirPath: string): Promise<void>;
}

/**
 * File operations service contract
 */
export interface IFileOperations {
  /**
   * Read file content
   */
  readFile(filePath: string): Promise<string>;

  /**
   * Write file content
   */
  writeFile(filePath: string, content: string): Promise<void>;

  /**
   * Delete file
   */
  deleteFile(filePath: string): Promise<void>;

  /**
   * Get file checksum
   */
  getChecksum(content: string): string;

  /**
   * Get file modification time
   */
  getModificationTime(filePath: string): Promise<Date>;
}

// ============================================================================
// Event Contracts
// ============================================================================

export type SyncEventType = 'file-added' | 'file-updated' | 'file-removed' | 'error' | 'complete';

export interface SyncEvent {
  type: SyncEventType;
  timestamp: Date;
  data?: any;
}

export interface ISyncEventEmitter {
  on(event: SyncEventType, handler: (data: any) => void): void;
  off(event: SyncEventType, handler: (data: any) => void): void;
  emit(event: SyncEventType, data?: any): void;
}

// ============================================================================
// CLI Command Contracts
// ============================================================================

export interface ICliCommands {
  /**
   * Run sync command
   */
  runSync(options: { clean?: boolean; validate?: boolean }): Promise<void>;

  /**
   * Run watch command
   */
  runWatch(): Promise<void>;

  /**
   * Run clean command
   */
  runClean(): Promise<void>;

  /**
   * Run validate command
   */
  runValidate(): Promise<void>;
}

// ============================================================================
// Configuration Defaults
// ============================================================================

export const DEFAULT_CONFIG: SyncConfiguration = {
  sourcePatterns: [
    {
      pattern: 'src/specify_cli/commands/*/docs.{md,mdx}',
      type: 'command',
      outputSubdir: 'reference/cli'
    },
    {
      pattern: 'src/specify_cli/services/*/docs.{md,mdx}',
      type: 'service',
      outputSubdir: 'reference/api'
    },
    {
      pattern: 'src/specify_cli/guides/*.{md,mdx}',
      type: 'guide',
      outputSubdir: 'guides'
    }
  ],
  outputDir: 'docs/docs',
  watch: false,
  clean: true,
  validate: true,
  preserveExtensions: true
};
