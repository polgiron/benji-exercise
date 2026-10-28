import eslintConfigPrettier from 'eslint-config-prettier'
import pluginVue from 'eslint-plugin-vue'
import globals from 'globals'
import tseslint from 'typescript-eslint'
import { config as baseConfig } from './base.js'

/**
 * Shared ESLint config for Vue packages and Nuxt apps.
 *
 * @type {import("eslint").Linter.Config[]}
 */
export const config = [
  ...baseConfig,
  ...pluginVue.configs['flat/recommended'],
  {
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: { parser: tseslint.parser, extraFileExtensions: ['.vue'] },
      globals: globals.browser,
    },
  },
  {
    rules: {
      // TypeScript already reports unknown names, and Nuxt auto-imports would trip this rule.
      'no-undef': 'off',
      // shadcn-vue components are single-word (Button, Card…) by convention.
      'vue/multi-word-component-names': 'off',
      // Optional props typed with TypeScript are `undefined` by design.
      'vue/require-default-prop': 'off',
    },
  },
  eslintConfigPrettier,
]
