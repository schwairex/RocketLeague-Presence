# v0.2.1 UI verification

Kept existing offline fonts, dark navy palette, blue/orange SVG identity, header,
Appearance, General form, diagnostics and persistent footer. Updates/About were
intentionally redesigned within those styles.

Updates: installed version, state/message, progress, retry/GitHub actions, three
update steps and chronological release notes. Remote text uses textContent.
About: logo, version, purpose, three feature cards, manual-data explanation and
developer/project/docs links. At 1120 × 760 the full About fits without scrolling.
At 940 × 680 content scrolls while Save/Cancel remain visible. No horizontal
overflow. General ID is read-only with no editable field binding; the backend
also ignores injected client_id. Focus indicators remain visible.

Browser QA verified both tabs and offline/404 update state with enabled retry.
No JS warnings/errors. about-v0.2.1.png and updates-v0.2.1.png contain isolated
fixture data; example release notes do not prove a remote release exists.
