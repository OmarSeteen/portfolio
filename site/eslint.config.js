import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";

export default [
  { ignores: ["dist", ".lighthouse"] },
  js.configs.recommended,
  reactHooks.configs.flat.recommended,
  {
    files: ["**/*.{js,jsx}"],
    languageOptions: {
      globals: globals.browser,
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    rules: {
      // ESLint's core rules cannot see that <App /> uses the App import.
      "no-unused-vars": ["error", { varsIgnorePattern: "^[A-Z_]" }],
      // React escapes every value it renders. This prop is the one way around that, and
      // the CV content comes from a form, so it stays banned.
      "no-restricted-syntax": [
        "error",
        {
          selector: "JSXAttribute[name.name='dangerouslySetInnerHTML']",
          message:
            "Render text as text. Raw HTML from content is how XSS gets in.",
        },
      ],
    },
  },
  {
    // Build and check scripts at the top of site/ run in Node, not in the browser.
    files: ["*.js"],
    languageOptions: { globals: globals.node },
  },
];
