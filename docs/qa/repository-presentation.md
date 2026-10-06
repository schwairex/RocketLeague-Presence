# Repository presentation — 2026-10-06

The v0.2.4 README and repository organization were refreshed using the supplied
logo. This documentation update does not change the app version or executable.

- The supplied logo is copied byte-for-byte to `assets/branding/logo.svg`.
- Hero and download graphics are self-contained SVGs; no scripts, embedded HTML
  or external image/font resources are used.
- English/Turkish README pages render with the existing bundled GFM parser.
  Five images load in each page; the screenshot gallery opens correctly.
- Both languages were checked at 1280px and 390px: no page-level horizontal
  overflow. The Turkish getting-started anchor scrolls to the correct section.
- 70 relative documentation/image links and Markdown section anchors resolve.
- 55 Python application, test, entry-point, build and configuration-example
  files match the previously repaired v0.2.4 source archive byte-for-byte.
- Detailed user guides, third-party license notices and historical QA records
  are preserved under `docs/`. Public branding/screenshots are under `assets/`.
- Current screenshots use isolated sample data; no real game INI, Discord
  activity or public issue report is changed during capture.

The browser preview approximates GitHub's Markdown styling. It is a local
verification, not a deployed GitHub page. Release availability and the direct
EXE button require the maintainer's published Release asset. Upload steps are
in [github-upload.tr.md](../github-upload.tr.md).

- The rebuilt source archive extracted successfully with Windows Expand-Archive;
  all 93 files matched the source tree. Its extracted application passed all
  **189 pytest tests**. A read-only independent review found no material issues.
