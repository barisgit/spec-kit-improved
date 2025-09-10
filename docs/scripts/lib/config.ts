import type { SyncConfiguration } from './types';

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
  outputDir: 'docs',
  watch: false,
  clean: true,
  validate: true,
  preserveExtensions: true
};