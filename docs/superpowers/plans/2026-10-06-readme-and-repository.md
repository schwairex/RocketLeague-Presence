# README and repository presentation plan

**Goal:** Present RL Presence clearly on GitHub using the supplied logo and keep
the source tree easy to navigate.

**Architecture:** Keep the existing Python package, tests, run.py and build.ps1
locations. Put public branding/screenshots under assets/, move long guides and
QA records under docs/, and preserve third-party license notices. Implement
locally; the user uploads the finished files to their existing repository.

**Constraints:** Version remains 0.2.4. No runtime behavior, dependencies or
Discord identity changes. English and Turkish README pages use relative image
links. Manual ranks and API limitations must be described accurately.

- [x] Preserve the original logo and prepare self-contained SVG presentation assets.
- [x] Organize existing documentation, license notices and QA images; update links.
- [x] Write matching English/Turkish README pages with download, first run,
      features, screenshots, troubleshooting, development and contributor links.
- [x] Capture the current desktop UI with clearly labeled sample data.
- [x] Explain web upload, GitHub Desktop, old-path removal and Release assets.
- [x] Validate relative Markdown/HTML links, SVGs, runtime-file hashes and pytest.
- [x] Rebuild the complete source ZIP atomically, verify Windows extraction and
      compare every extracted source file before delivery.

**Review focus:** Images must render without external SVG resources; moving
docs must not break links; the EXE belongs in Releases; user config/logs/cache
must stay out of GitHub; Python package/build paths must remain usable.
