# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

- Add durable project-specific notes here as they are discovered through real work.

## Site notes

Hand-written static site served by GitHub Pages. No build step, no dependencies, no
package manager: `index.html`, `work-in-progress.html`, `projects.html`,
`contact.html`, plus one shared `styles.css` and one shared `script.js`.

- Assets are cache-busted by query string (`styles.css?v=N`, `script.js?v=N`).
  When you change either file, bump the version on **every** page that links it,
  or returning visitors keep the stale copy.
- Nav is duplicated by hand in each page's `<header class="nav">` (the landing page
  uses `nav.intro__links` in the body instead). There is no include mechanism, so a
  nav change means editing all four files and marking the current page with
  `class="is-here" aria-current="page"`.
- Verify changes in a browser, not by reading markup. There is no test suite.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
