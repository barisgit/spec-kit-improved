import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  // Main documentation sidebar
  docsSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Guides',
      items: [
        'guides/installation', 
        'guides/quickstart',
        'guides/workflow',
      ],
    },
    {
      type: 'category',
      label: 'About',
      items: [
        'about/philosophy',
      ],
    },
  ],

  // Reference documentation sidebar
  referenceSidebar: [
    {
      type: 'category',
      label: 'CLI Commands',
      items: [
        'reference/cli/init',
        'reference/cli/check',
      ],
    },
    // { TODO: Uncomment when API is implemented
    //   type: 'category',
    //   label: 'API',
    //   items: [],
    // },
  ],
};

export default sidebars;
