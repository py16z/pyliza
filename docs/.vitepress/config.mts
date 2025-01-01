import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "pyliza",
  description: "Conversational Agent for Twitter and Discord",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Quick Start', link: '/quick-start' }
    ],

    sidebar: [
      {
        text: 'Docs',
        items: [
          // { text: 'Markdown Examples', link: '/markdown-examples' },
          { text: 'Quick Start', link: '/quick-start' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/py16z/pyliza' }
    ]
  }
})
