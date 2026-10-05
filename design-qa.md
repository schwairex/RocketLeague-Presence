# Design QA — v0.2

Source: user-supplied `C:/Users/Berkay/Downloads/Rocket League RPC – Arayüz Tasarımı.html`, extracted into inert HTML without executing bundled scripts. `ui-source.png` captures the source with original fonts/SVGs.

Implementation: `rocket_league_rpc/ui/index.html` + `app.js`, shared by browser verification and native WebView2. Evidence: `ui-implementation.png`, `ui-general.png`, `ui-small.png`, `ui-comparison.png`, `ui-detail-comparison.png`.

Viewport/state: 1120 × 760 CSS px, DPR 1; source and implementation images are both 1120 × 760 pixels. Simulated 2–1 match, 3:42, DFH Stadium/Ranked 2v2 and supplied sample player/log copy. Fixtures exist only in the temporary QA server; production never populates live values with samples. Native EXE client size independently verified as 1120 × 760. Minimum responsive viewport tested: 940 × 680.

**Comparison history and findings**

- Initial captures had different effective viewport sizes; recaptured both at 1120 × 760, DPR 1 before comparing.
- [P2, fixed] A global border-box rule and minimum card height changed the supplied badge/card proportions. Removed both rules and retained original content sizing. Post-fix full-view evidence: `ui-comparison.png`; focused evidence: `ui-detail-comparison.png`. Both comparisons were viewed with source left and implementation right.
- [P2, fixed] WinForms initially reduced native client dimensions to 1104 × 721. Resized once after removing its frame. Actual EXE now reports 1120 × 760 in `release-smoke.json`.
- No remaining actionable P0/P1/P2 visual findings. Stats API dot intentionally becomes green for live packets instead of the source's static yellow sample. Live preview, General settings and diagnostics are functional extensions.

**Required fidelity surfaces**

| Surface | Result |
|---|---|
| Fonts/typography | Original Barlow Condensed and DM Sans embedded offline; original weights, sizes, line heights, letter spacing and wrapping retained. Focused preview/card text inspected at 1:1 density. |
| Spacing/layout | Original 40/72/72 title/header/footer, 28px gutters, 400px right column, row/toggle geometry, padding and radii retained at reference size. Responsive minimum retains Save/Cancel without horizontal overflow. |
| Colors/tokens | Source background/border/text palette, blue #3D8BFF and orange #FF8F2B retained. Semantic connection colors change with telemetry. |
| Assets | Supplied SVGs reused directly; original font data embedded. No generated approximations. Generic preview states reuse the source's header mark. Actual Discord arena artwork must be uploaded through the Developer Portal; source's field icon remains the illustrative map preview. |
| Copy/content | Original Turkish UI labels retained. Runtime scores/logs/status and outgoing RPC text replace demo values. General explains manual fields. Preview samples never publish. |

**Interactions and errors**

Browser verified toggles, Save, Cancel, rank/division/manual shop selection, all four tabs, menu/replay preview, diagnostics open/close and minimum viewport. Console warning/error inspection returned no entries. Settings persistence, failure handling and hot reload are covered by Python tests. Actual native EXE bridge exercised without real Discord credentials.

Remaining test gaps: uploaded Discord art/per-user ID, other Windows systems lacking WebView2/.NET, real overtime direction and other arena/playlist variations. These do not alter the visual comparison.

final result: passed
