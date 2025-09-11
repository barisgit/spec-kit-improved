/**
 * Type definitions for the documentation synchronization system
 */

export type DocumentationType = 'command' | 'service' | 'guide' | 'about' | 'contributing';

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

export type SyncEventType = 'file-added' | 'file-updated' | 'file-removed' | 'error' | 'complete';

export interface SyncEvent {
  type: SyncEventType;
  timestamp: Date;
  data?: any;
}