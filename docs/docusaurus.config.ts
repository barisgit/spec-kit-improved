import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// Omit index documents from the sidebar
function omitIndexDocuments(items: any[], parentCategoryLink: any = null): any[] {
  // Process items in categories
  const result = items.map((item) => {
    if (item.type === 'category') {
      return {...item, items: omitIndexDocuments(item.items || [], item.link)};
    }
    return item;
  });
  
  // Omit index documents at current level
  return result.filter((item) => {
    // Filter out items with docId 'index' or items that end with '/index'
    if (item.docId === 'index' || item.docId?.endsWith('/index')) {
      return false;
    }
    
    // Also check the id property for index documents
    if (item.id === 'index' || item.id?.endsWith('/index')) {
      return false;
    }
    
    // Filter out items that have the same URL as the parent category
    if (parentCategoryLink && item.type === 'doc') {
      const itemId = item.docId || item.id;
      if (itemId) {
        const itemUrl = `/${itemId}/`;
        const categoryUrl = parentCategoryLink.type === 'doc' ? `/${parentCategoryLink.id}/` : null;
        if (categoryUrl && itemUrl === categoryUrl) {
          return false;
        }
      }
    }
    
    return true;
  });
}

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: 'SpecifyX Documentation',
  tagline: 'Enhanced spec-driven development CLI with modern architecture',
  favicon: 'img/favicon.ico',

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  // Set the production url of your site here
  url: 'https://specifyx.dev',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'barisgit', // Usually your GitHub org/user name.
  projectName: 'spec-kit-improved', // Usually your repo name.

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/barisgit/spec-kit-improved/tree/main/docs/',
          async sidebarItemsGenerator({defaultSidebarItemsGenerator, ...args}) {
            const sidebarItems = await defaultSidebarItemsGenerator(args);
            return omitIndexDocuments(sidebarItems);
          },
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Replace with your project's social card
    image: 'img/docusaurus-social-card.jpg',
    navbar: {
      title: 'SpecifyX',
      logo: {
        alt: 'SpecifyX Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          type: 'docSidebar',
          sidebarId: 'referenceSidebar',
          position: 'left',
          label: 'Reference',
        },
        {
          type: 'docSidebar',
          sidebarId: 'contributingSidebar',
          position: 'left',
          label: 'Contributing',
        },
        {
          href: 'https://github.com/barisgit/spec-kit-improved',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Links',
          items: [
            {
              label: 'Docs',
              to: '/docs/intro',
            },
            {
              label: 'Reference',
              to: '/docs/reference/cli/init',
            },
          ],
        },
        // {
        //   title: 'Community',
        //   items: [
        //     {
        //       label: 'Stack Overflow',
        //       href: 'https://stackoverflow.com/questions/tagged/docusaurus',
        //     },
        //     {
        //       label: 'Discord',
        //       href: 'https://discordapp.com/invite/docusaurus',
        //     },
        //     {
        //       label: 'X',
        //       href: 'https://x.com/docusaurus',
        //     },
        //   ],
        // },
        {
          title: 'More',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/barisgit/spec-kit-improved',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} SpecifyX, Inc. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'bash'],
    },
  } satisfies Preset.ThemeConfig,
  plugins: [
    [
      require.resolve('docusaurus-lunr-search'),
      {
        languages: ['en'],
      },
    ],
  ],
};

export default config;
