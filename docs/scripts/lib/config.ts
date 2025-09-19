import type { SyncConfiguration } from './types';

/**
 * Default synchronization configuration used by documentation tooling.
 */
export const DEFAULT_CONFIG: SyncConfiguration = {
  sourcePatterns: [
    {
      pattern: '../src/specify_cli/commands/*/docs.{md,mdx}',
      type: 'command',
      outputSubdir: 'docs/reference/cli'
    },
    {
      pattern: '../src/specify_cli/services/*/docs.{md,mdx}',
      type: 'service',
      outputSubdir: 'docs/reference/api'
    },
    {
      pattern: '../src/specify_cli/assistants/*/docs.{md,mdx}',
      type: 'assistant',
      outputSubdir: 'docs/reference/assistants'
    },
    {
      pattern: '../src/specify_cli/guides/*.{md,mdx}',
      type: 'guide',
      outputSubdir: 'docs/guides'
    },
    {
      pattern: '../src/specify_cli/about/*.{md,mdx}',
      type: 'about',
      outputSubdir: 'docs/about'
    },
    {
      pattern: '../src/specify_cli/contributing/*.{md,mdx}',
      type: 'contributing',
      outputSubdir: 'docs/contributing'
    },
    {
      pattern: '../architecture/*.mdx',
      type: 'architecture',
      outputSubdir: 'docs/architecture'
    }
  ],
  outputDir: 'docs/docs',
  watch: false,
  clean: true,
  validate: true,
  preserveExtensions: true
};
