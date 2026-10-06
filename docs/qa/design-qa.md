# v0.2.4 design verification

Final result: **pass** after two visual iterations.

Both supplied HTML references were opened locally and captured. Source and
implementation captures were combined side by side for Updates and About.
Existing DM Sans/Barlow Condensed fonts, navy/blue palette, logo, custom
titlebar, header/navigation and 72px footer were preserved as requested.

Initial findings and corrections:
- Appearance's important grid display overrode hidden. A scoped rule now
  guarantees exactly one visible page.
- Turkish uppercase İ prevented Improvement headings from being categorized.
  Normalization now produces Yeni / İyileştirme / Düzeltme rows correctly.
- Semantic tag fills match the reference more closely using existing dark
  green/brown colors; text remains accessible.
- Live text is only mutated when changed, avoiding identical repeated announcements.

Fidelity surfaces:
- Typography: existing embedded offline fonts; notes 13px/19.5px, tags 78px,
  feature titles 14px/500 and descriptions 12px.
- Layout: internal card actions/divider/check time, version cards/badges/date,
  collapsed history; horizontal hero/actions, equal feature cards, control CTA
  and developer avatar rows. Taller content scrolls without overlap.
- Color: only existing palette. Muted copy contrast 7.63:1, card copy 11.62,
  blue tags 6.73 and primary-button dark text 5.61. Green/yellow tags also pass AA.
- Assets: original logo; reference-style Tabler SVGs bundled with MIT license.
- Copy: actual version/notes replace static v0.2.3 examples. Turkish/English
  labels; original GitHub notes retain their language and render as safe text.

Functional evidence: 30 browser cases covering five tabs, both languages,
900×640 / 1120×760 / 1600×1000 with no horizontal overflow. History retains its
expanded state across refresh and defaults closed. All update phases/error,
disabled actions, hidden current-state progress, inert script-like notes,
About → General, connected/disconnected footer and 2px keyboard focus passed.
Save/Cancel only appear on Appearance/General. No browser warnings/errors.
Native window checks are in verification.md / release-smoke.json.

Expected differences: reference lacks the OS titlebar and uses exported font/
color values and static notes. Existing app chrome/fonts/palette and real
v0.2.4 data take precedence under the user's explicit constraints. Portal
rank bitmap uploads are separate per the user's keys/list-only clarification.
