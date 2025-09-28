#!/usr/bin/env tsx

import { readFile, writeFile, mkdir } from 'fs/promises';
import { resolve, join } from 'path';
import chalk from 'chalk';

/**
 * Convert comprehensive JSON metadata to MDX files
 * Auto-generates docs for commands, services, assistants, and utils
 */

interface DocstringInfo {
  summary: string;
  description: string;
  args: Record<string, string>;
  returns: string;
  raises: Record<string, string>;
  examples: string[];
  notes: string[];
  raw: string;
}

interface ParameterInfo {
  name: string;
  type_annotation: string;
  default_value: string | null;
  is_required: boolean;
  description: string;
}

interface MethodInfo {
  name: string;
  signature: string;
  docstring: DocstringInfo;
  parameters: ParameterInfo[];
  return_type: string;
  is_async: boolean;
  is_property: boolean;
  is_classmethod: boolean;
  is_staticmethod: boolean;
}

interface ClassInfo {
  name: string;
  module_path: string;
  docstring: DocstringInfo;
  methods: MethodInfo[];
  properties: string[];
  inheritance: string[];
  is_abstract: boolean;
  is_dataclass: boolean;
  is_enum: boolean;
}

interface ModuleInfo {
  name: string;
  file_path: string;
  docstring: DocstringInfo;
  classes: Record<string, ClassInfo>;
  functions: Record<string, MethodInfo>;
  constants: Record<string, { value: string; type: string }>;
}


interface Metadata {
  project: {
    name: string;
    version: string;
    description: string;
  };
  generated_at: string;
  generation_timestamp: string;
  modules: {
    commands: Record<string, ModuleInfo>;
    services: Record<string, ModuleInfo>;
    models: Record<string, ModuleInfo>;
    assistants: Record<string, ModuleInfo>;
    utils: Record<string, ModuleInfo>;
    core: Record<string, ModuleInfo>;
    other: Record<string, ModuleInfo>;
  };
  stats: {
    total_modules: number;
    total_classes: number;
    total_functions: number;
  };
}

function formatTitle(name: string): string {
  return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function createUniqueModuleNames(modules: Record<string, ModuleInfo>): Record<string, string> {
  const nameMap: Record<string, string> = {};
  const nameCount: Record<string, string[]> = {};

  // First pass: collect all base names and their full module paths
  for (const modulePath of Object.keys(modules)) {
    const parts = modulePath.split('.');
    const baseName = parts[parts.length - 1];

    if (!nameCount[baseName]) {
      nameCount[baseName] = [];
    }
    nameCount[baseName].push(modulePath);
  }

  // Second pass: generate unique names
  for (const [baseName, modulePaths] of Object.entries(nameCount)) {
    if (modulePaths.length === 1) {
      // No duplicates, use base name
      nameMap[modulePaths[0]] = baseName;
    } else {
      // Handle duplicates by using more path context
      for (const modulePath of modulePaths) {
        const parts = modulePath.split('.');
        // Use last two parts for context (e.g., "claude_provider" instead of just "provider")
        const uniqueName = parts.length >= 2
          ? `${parts[parts.length - 2]}_${parts[parts.length - 1]}`
          : parts[parts.length - 1];
        nameMap[modulePath] = uniqueName;
      }
    }
  }

  return nameMap;
}

function sanitizeContent(content: string): string {
  if (!content) return content;

  // Clean up problematic content that breaks MDX
  return content
    // Remove typer object references completely
    .replace(/<[^>]*\.models\.[^>]*object at 0x[^>]*>/g, '[typer object]')
    // Clean class references
    .replace(/<class '([^']+)'>/g, '$1')
    // Replace memory addresses
    .replace(/0x[0-9a-f]+/g, '...')
    // Wrap remaining angle bracket content in code
    .replace(/<([^>]+)>/g, '`<$1>`')
    // Wrap curly braces in code
    .replace(/\{([^}]+)\}/g, '`{$1}`')
    // Handle markdown links - validate and clean
    .replace(/\[([^\]]*)\]\(([^)]*)\)/g, (match, text, url) => {
      // Check if it's a relative link that starts with ../ (going up directories)
      if (url.startsWith('../')) {
        // For relative links going up directories, convert to plain text to avoid broken links
        // These are typically auto-generated Pydantic docs links that don't exist in this project
        return text;
      }

      // Clean .mdx extensions from valid links
      const cleanUrl = url.replace(/\.mdx$/, '');
      return `[${text}](${cleanUrl})`;
    });
}

function sanitizeSignature(signature: string): string {
  if (!signature) return signature;

  return signature
    .replace(/0x[0-9a-f]+/g, '...')  // Replace memory addresses
    .replace(/<([^>]+)>/g, '`<$1>`')  // Wrap angle bracket content in code
    .replace(/\{([^}]+)\}/g, '`{$1}`'); // Wrap curly braces in code
}

function cleanModuleName(moduleName: string): string {
  return moduleName.split('.').pop() || moduleName;
}

function shouldSkipModule(category: string, moduleName: string, module: ModuleInfo): boolean {
  const cleanName = cleanModuleName(moduleName);


  // Skip modules with no significant content
  const hasSignificantContent = Object.keys(module.classes).length > 0 ||
                                Object.keys(module.functions).length > 2; // Allow some utility functions

  if (!hasSignificantContent) return true;

  // Skip utility/internal modules that are not main APIs
  const skipPatterns = [
    'constants', 'types', 'validator', 'error_formatter', 'logging_config',
    'keyboard_input', 'interactive_menu', 'file_operations', 'script_helpers',
    'helpers', 'validation_service', 'path_resolver', 'agent_name_extractor'
  ];

  if (skipPatterns.some(pattern => cleanName.includes(pattern))) return true;

  // Only include main service classes, not every submodule
  if (category === 'services') {
    // Skip if it doesn't end with 'service' or isn't a main service
    if (!cleanName.includes('service') && !['config', 'project_manager'].includes(cleanName)) {
      return true;
    }
  }

  // Skip internal utilities and test files
  if (category === 'utils' && (cleanName.includes('test') || cleanName.includes('__'))) {
    return true;
  }

  return false;
}

function shouldSkipMethod(method: MethodInfo, className: string): boolean {
  // Skip Click/Typer framework methods that are inherited
  const frameworkMethods = [
    'add_command', 'collect_usage_pieces', 'command', 'format_commands',
    'format_epilog', 'format_help', 'format_help_text', 'format_options',
    'format_usage', 'get_command', 'get_help', 'get_help_option',
    'get_help_option_names', 'get_params', 'get_short_help_str', 'get_usage',
    'group', 'invoke', 'list_commands', 'main', 'make_context', 'make_parser',
    'parse_args', 'resolve_command', 'result_callback', 'shell_complete',
    'to_info_dict'
  ];

  if (frameworkMethods.includes(method.name)) return true;

  // Skip framework classes entirely
  if (className.includes('Group') || className.includes('Banner') || className.includes('Command')) {
    return true;
  }

  // Skip methods with generic or empty descriptions
  if (!method.docstring.summary ||
      method.docstring.summary === 'No description available' ||
      method.docstring.summary.length < 5) {
    return true;
  }

  // Skip dunder methods and private methods
  if (method.name.startsWith('_')) return true;

  return false;
}

function shouldSkipClass(classInfo: ClassInfo): boolean {
  const className = classInfo.name;

  // Skip framework classes
  const frameworkClasses = ['BannerGroup', 'TyperGroup', 'Command', 'Group'];
  if (frameworkClasses.includes(className)) return true;

  // Skip classes with no useful methods
  const usefulMethods = classInfo.methods.filter(m => !shouldSkipMethod(m, className));
  if (usefulMethods.length === 0 && classInfo.properties.length === 0) return true;

  return false;
}

async function generateModuleMdx(category: string, moduleName: string, module: ModuleInfo, outputDir: string, uniqueName: string): Promise<void> {
  // Skip modules that shouldn't be documented
  if (shouldSkipModule(category, moduleName, module)) {
    return;
  }

  const title = formatTitle(uniqueName);

  const frontmatter = {
    title: title,
    description: module.docstring.summary || `${title} module`,
    category: category,
    tags: [uniqueName, category, 'api'],
    generated: true,
    generated_at: new Date().toISOString(),
    module_path: moduleName
  };

  let content = `---
${Object.entries(frontmatter).map(([key, value]) => {
  if (key === 'tags' && Array.isArray(value)) {
    return `${key}: [${value.map(tag => `"${tag}"`).join(', ')}]`;
  }
  return `${key}: ${typeof value === 'string' ? `"${value}"` : value}`;
}).join('\n')}
---

# ${title}

${sanitizeContent(module.docstring.summary || `${title} module`)}

`;

  if (module.docstring.description) {
    content += `## Overview

${sanitizeContent(module.docstring.description)}

`;
  }

  // Classes section - filter out framework classes
  const classes = Object.entries(module.classes).filter(([_, classInfo]) => !shouldSkipClass(classInfo));
  if (classes.length > 0) {
    content += `## Classes

`;
    for (const [className, classInfo] of classes) {
      content += `### ${className}

${sanitizeContent(classInfo.docstring.summary || 'No description available')}

`;

      if (classInfo.inheritance.length > 0) {
        content += `**Inherits from:** ${classInfo.inheritance.join(', ')}

`;
      }

      if (classInfo.is_abstract) {
        content += `**Abstract class**

`;
      }

      if (classInfo.is_dataclass) {
        content += `**Dataclass**

`;
      }

      if (classInfo.is_enum) {
        content += `**Enum**

`;
      }

      if (classInfo.docstring.description) {
        content += `${sanitizeContent(classInfo.docstring.description)}

`;
      }

      // Methods - filter out framework methods
      const usefulMethods = classInfo.methods.filter(method => !shouldSkipMethod(method, className));
      if (usefulMethods.length > 0) {
        content += `#### Methods

`;
        for (const method of usefulMethods) {
          content += `##### ${method.name}

\`\`\`python
${sanitizeSignature(method.signature)}
\`\`\`

${sanitizeContent(method.docstring.summary)}

`;

          // Only show parameters if there are meaningful ones (not just self)
          const meaningfulParams = method.parameters.filter(p => p.name !== 'self' && p.name !== 'cls');
          if (meaningfulParams.length > 0) {
            content += `**Parameters:**

`;
            for (const param of meaningfulParams) {
              // Clean up type annotation to avoid MDX parsing issues
              const cleanType = param.type_annotation.replace(/^<class '([^']+)'>$/, '$1').replace(/'/g, '');
              content += `- \`${param.name}\` (${cleanType}${param.is_required ? ', required' : ', optional'})`;
              if (param.description) {
                content += ` - ${sanitizeContent(param.description)}`;
              }
              if (param.default_value && param.default_value !== 'None') {
                content += ` - Default: \`${sanitizeContent(param.default_value)}\``;
              }
              content += '\n';
            }
            content += '\n';
          }

          if (method.return_type && method.return_type !== 'Any' && method.return_type !== 'None') {
            content += `**Returns:** ${method.return_type}

`;
          }

          if (method.docstring.description &&
              method.docstring.description !== method.docstring.summary &&
              method.docstring.description.length > 10) {
            content += `${sanitizeContent(method.docstring.description)}

`;
          }
        }
      }

      // Properties
      if (classInfo.properties.length > 0) {
        content += `#### Properties

`;
        for (const prop of classInfo.properties) {
          content += `- \`${prop}\`\n`;
        }
        content += '\n';
      }
    }
  }

  // Functions section - filter out utility functions
  const functions = Object.entries(module.functions).filter(([funcName, funcInfo]) => {
    // Skip functions with no useful description
    if (!funcInfo.docstring.summary ||
        funcInfo.docstring.summary === 'No description available' ||
        funcInfo.docstring.summary.length < 5) {
      return false;
    }

    // Skip private functions
    if (funcName.startsWith('_')) return false;

    return true;
  });

  if (functions.length > 0) {
    content += `## Functions

`;
    for (const [funcName, funcInfo] of functions) {
      content += `### ${funcName}

\`\`\`python
${sanitizeSignature(funcInfo.signature)}
\`\`\`

${sanitizeContent(funcInfo.docstring.summary)}

`;

      // Only show meaningful parameters
      const meaningfulParams = funcInfo.parameters.filter(p => p.name !== 'self' && p.name !== 'cls');
      if (meaningfulParams.length > 0) {
        content += `**Parameters:**

`;
        for (const param of meaningfulParams) {
          // Clean up type annotation to avoid MDX parsing issues
          const cleanType = param.type_annotation.replace(/^<class '([^']+)'>$/, '$1').replace(/'/g, '');
          content += `- \`${param.name}\` (${cleanType}${param.is_required ? ', required' : ', optional'})`;
          if (param.description) {
            content += ` - ${sanitizeContent(param.description)}`;
          }
          if (param.default_value && param.default_value !== 'None') {
            content += ` - Default: \`${sanitizeContent(param.default_value)}\``;
          }
          content += '\n';
        }
        content += '\n';
      }

      if (funcInfo.return_type && funcInfo.return_type !== 'Any' && funcInfo.return_type !== 'None') {
        content += `**Returns:** ${funcInfo.return_type}

`;
      }

      if (funcInfo.docstring.description &&
          funcInfo.docstring.description !== funcInfo.docstring.summary &&
          funcInfo.docstring.description.length > 10) {
        content += `${sanitizeContent(funcInfo.docstring.description)}

`;
      }
    }
  }

  // Constants section
  const constants = Object.entries(module.constants);
  if (constants.length > 0) {
    content += `## Constants

`;
    for (const [constName, constInfo] of constants) {
      content += `- \`${constName}\` (${constInfo.type}) = \`${constInfo.value}\`\n`;
    }
    content += '\n';
  }

  const outputPath = join(outputDir, 'docs/reference', category, `${uniqueName}.mdx`);
  await mkdir(join(outputDir, 'docs/reference', category), { recursive: true });
  await writeFile(outputPath, content, 'utf-8');
  console.log(`${chalk.green('Generated')} ${category}: ${chalk.cyan(uniqueName + '.mdx')}`);
}

async function generateIndexMdx(category: string, modules: Record<string, ModuleInfo>, outputDir: string, uniqueNames: Record<string, string>): Promise<void> {
  const title = formatTitle(category);

  const frontmatter = {
    title: title,
    description: `Overview of all ${category} modules`,
    category: category,
    tags: [category, 'index', 'overview'],
    generated: true,
    generated_at: new Date().toISOString()
  };

  let content = `---
${Object.entries(frontmatter).map(([key, value]) => {
  if (key === 'tags' && Array.isArray(value)) {
    return `${key}: [${value.map(tag => `"${tag}"`).join(', ')}]`;
  }
  return `${key}: ${typeof value === 'string' ? `"${value}"` : value}`;
}).join('\n')}
sidebar_position: 1
---

# ${title}

Overview of all ${category} modules in SpecifyX.

## Available Modules

`;

  // Filter modules using the same logic as individual generation
  const filteredModules = Object.entries(modules).filter(([moduleName, module]) =>
    !shouldSkipModule(category, moduleName, module)
  );

  for (const [moduleName, module] of filteredModules) {
    const uniqueName = uniqueNames[moduleName];
    const moduleTitle = formatTitle(uniqueName);
    content += `### [${moduleTitle}](./${uniqueName})

${sanitizeContent(module.docstring.summary || 'No description available')}

`;
  }

  const outputPath = join(outputDir, 'docs/reference', category, 'index.mdx');
  await mkdir(join(outputDir, 'docs/reference', category), { recursive: true });
  await writeFile(outputPath, content, 'utf-8');
  console.log(`${chalk.green('Generated')} ${category} ${chalk.cyan('index')}`);
}

async function main(): Promise<void> {
  const metadataPath = resolve(__dirname, '../metadata.json');
  const outputDir = resolve(__dirname, '..');

  try {
    const metadataContent = await readFile(metadataPath, 'utf-8');
    const metadata: Metadata = JSON.parse(metadataContent);

    console.log(`${chalk.hex('#FFA500')('Converting')} comprehensive JSON metadata to ${chalk.cyan('MDX')} files...`);
    console.log(`Processing ${chalk.magenta(metadata.stats.total_modules)} modules, ${chalk.magenta(metadata.stats.total_classes)} classes, ${chalk.magenta(metadata.stats.total_functions)} functions`);


    // Generate module docs for each category
    const categories = ['services', 'assistants', 'models', 'utils', 'core'] as const;

    for (const category of categories) {
      const modules = metadata.modules[category];
      if (Object.keys(modules).length > 0) {
        console.log(`\n${chalk.hex('#FFA500')('Generating')} ${chalk.cyan(category)} modules...`);

        // Create unique names for this category to avoid duplicates
        const uniqueNames = createUniqueModuleNames(modules);

        // Generate individual module docs and track what we actually generated
        const generatedModules: string[] = [];
        for (const [moduleName, module] of Object.entries(modules)) {
          if (!shouldSkipModule(category, moduleName, module)) {
            const uniqueName = uniqueNames[moduleName];
            await generateModuleMdx(category, moduleName, module, outputDir, uniqueName);
            generatedModules.push(moduleName);
          }
        }

        // Only generate index if we have modules to show
        if (generatedModules.length > 0) {
          const filteredModules = Object.fromEntries(
            generatedModules.map(name => [name, modules[name]])
          );
          const filteredUniqueNames = Object.fromEntries(
            generatedModules.map(name => [name, uniqueNames[name]])
          );
          await generateIndexMdx(category, filteredModules, outputDir, filteredUniqueNames);
        }
      }
    }

    // Generate main index
    const mainIndexContent = `---
title: Generated API Documentation
description: Auto-generated documentation from SpecifyX source code
category: index
generated: true
generated_at: ${new Date().toISOString()}
sidebar_position: 1
---

# Generated API Documentation

This documentation is automatically generated from the SpecifyX source code.

## Statistics

- **Total Modules**: ${metadata.stats.total_modules}
- **Total Classes**: ${metadata.stats.total_classes}
- **Total Functions**: ${metadata.stats.total_functions}

## Categories

${categories.map(cat => {
  const count = Object.keys(metadata.modules[cat]).length;
  return count > 0 ? `- [${formatTitle(cat)}](./${cat}/) (${count} modules)` : null;
}).filter(Boolean).join('\n')}

---

*Generated on ${new Date().toISOString()} from ${metadata.project.name} v${metadata.project.version}*
`;

    await writeFile(join(outputDir, 'docs/reference/index.mdx'), mainIndexContent, 'utf-8');
    console.log(`\n${chalk.green('Generated')} main ${chalk.cyan('index')}`);

    console.log(`\n${chalk.green('All')} ${chalk.cyan('MDX')} files generated ${chalk.green('successfully')}!`);
    console.log(`Output directory: ${chalk.gray(join(outputDir, 'docs/reference'))}`);

  } catch (error) {
    console.error(`${chalk.red('Error:')}`, error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}