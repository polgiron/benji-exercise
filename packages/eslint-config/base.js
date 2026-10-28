import js from '@eslint/js'
import eslintConfigPrettier from 'eslint-config-prettier'
import onlyWarn from 'eslint-plugin-only-warn'
import turboPlugin from 'eslint-plugin-turbo'
import globals from 'globals'
import tseslint from 'typescript-eslint'

/**
 * Shared ESLint config for every TypeScript package.
 * Everything reports as a warning; packages lint with `--max-warnings 0`.
 *
 * @type {import("eslint").Linter.Config[]}
 */
export const config = [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    plugins: { turbo: turboPlugin },
    rules: { 'turbo/no-undeclared-env-vars': 'warn' },
  },
  {
    plugins: { onlyWarn },
  },
  {
    rules: {
      '@typescript-eslint/no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_' },
      ],
      '@typescript-eslint/consistent-type-imports': 'warn',
    },
  },
  {
    files: ['**/*.mjs', '**/*.cjs', '**/*.config.{js,ts}', 'scripts/**'],
    languageOptions: { globals: globals.node },
  },
  {
    ignores: ['dist/**', 'coverage/**', '.turbo/**', '.nuxt/**', '.output/**', '.data/**'],
  },
  // Last: turns off the rules Prettier owns.
  eslintConfigPrettier,
]
