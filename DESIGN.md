# Design

<!-- impeccable:design-schema 1 -->

## World

**Standard Mark.** Every recommendation renders as a struck certification seal, not a search-result card. The confidence ring (`Seal.jsx`) is the signature device: a circular medallion whose inner arc sweep and fill *encodes* the HIGH/MEDIUM/LOW confidence tier rather than decorating next to it. It anchors every result card (46px, in the "medallion strip" header) and every detail modal (42px).

The brand mark itself — header, hero watermark, trust card — is the real BIS emblem (`public/bis-logo.png`), not an invented abstraction, per direct user steering: "its better to use this logo and the accent of the colors from the logo." The invented `Seal` device is reserved for what it actually encodes (per-standard confidence), never stands in for the organization.

Chosen over the rolled assignment (Platform Signage — riveted railway/PWD enamel plates) after the user steered away from anything "too techy" (which also ruled out a competitive Night Instrument Panel / aircraft-gauge alternate) and asked explicitly for white + BIS blue, "comfortable, safe, secured," no neon, no techy edges. The hackathon-specific chrome from the first pass — a dark utility strap reading "Smart India Hackathon 2026 · Problem Statement 26108" and a footer disclaimer line — was removed on the same request; the language toggle it held moved into the main header row.

## Palette — Restrained, sampled from the emblem

White ground (`--paper #FFFFFF`, `--paper-sunken #F5F8FC`) plus two colors sampled directly from `bis-logo.png` by pixel count (`scripts` in that session: PIL dominant-color extraction against a white-composited background): logo blue `#0C4DA1` (8.1:1 on white) is `--seal`, used as-is. Logo red `#ED1B24` (4.39:1 on white, just under AA body-text minimum) is darkened ~10% to `#D51820` (5.28:1) for `--danger`, so compliance-fail states read as the emblem's own red rather than an invented brick-red. One amber (`--gold` / `--warn`, both `#8A6A12` — originally two near-duplicate hues, consolidated after finish review flagged the dilution) covers both mandatory-certification and currency/superseded warnings, differentiated by icon and label, not hue. Success-green is reserved narrowly for compliance status. No violet, no neon, no second amber — five hue families total including ink/neutral, two of which (blue, red) are the organization's own.

`--ink-muted` is `#64708A` (4.97:1 on white) — not the original `#8592A6` (3.15:1), which failed the craft floor's 4.5:1 body-text minimum and was caught in finish review.

## Type

Self-hosted (no external font CDN, `frontend/public/fonts/`, `@font-face` in `index.css`) — required for the product's own offline-first claim. **Plex Sans** (IBM Plex Sans) for UI text and headings — a workhorse grotesk appropriate to Operate mode, not a system-font fallback. **Plex Mono** (IBM Plex Mono) for IS codes, confidence scores, quantities — genuine data/measurement, not a "technical" costume. **Plex Devanagari** loads alongside Plex Sans specifically because the product's real multilingual-input requirement (Hindi/Marathi/Tamil/etc.) needed a family with genuine Devanagari support, not an afterthought.

## Components

- **Seal** (`components/Seal.jsx`) — the confidence-ring device. Props: `tier` (`high`/`medium`/`low`, plus an unused `brand` kept for API completeness), `size`. Renders a struck-ring SVG with a dashed inner engraving ring and an arc whose sweep is 1.0 / 0.55 / 0.22 for high/medium/low.
- **BIS emblem** (`public/bis-logo.png`) — the real brand mark, used as an `<img>` wherever the product identifies itself: the header (38px), the trust card (52px), and a 340px low-opacity hero watermark. Colors token'd off it directly (see Palette).
- **Card medallion strip** (`.card-medallion-strip` in `StandardCard.jsx`) — a tinted header band (Seal + IS code + confidence label + schedule category on the left, edition/superseded/amendment badges on the right) separated from the card body by a hairline rule. Not a small paired icon; the seal is the header's own weight-bearing element.
- **Trust card seal header** (`.trust-seal-header` in `SpecSearch.jsx`) — the live-registry stat card leads with the emblem, matching the FIRST VIEWPORT promise that this card "carries the same seal-ring styling."
- **Hero watermark** (`.hero-watermark-seal`) — the emblem at 340px / 7% opacity behind the headline, establishing the world before any search happens (the "memory test": what would a visitor remember an hour after a one-second glance).
- Badges, ribbons (QCO/superseded/schedule), allied-standard tags, modal tabs, the officer table (tender auditor), and the terminal-style console (benchmark sandbox) all draw from the same token set — no component introduces its own one-off color.

## Motion

One authored moment: `seal-strike` — cards and modals enter with a quick scale-and-settle (0.97→1, translateY 6px→0, `cubic-bezier(0.16,1,0.3,1)`), staggered ~60ms per card in a result list. No scattered hover effects beyond ordinary state transitions (border/shadow/color, all ≤0.2s).

## States & accessibility

Hover/disabled/loading/error/empty all styled per-component (search button, action buttons, chips, cap-cards, trust-skeleton pulse, error-banner, empty-state-box). `:focus-visible` themed globally. Browser surfaces themed: `::selection`, `::-webkit-scrollbar`, `caret-color`, `accent-color`. Both modals (`StandardDetailsModal`, `GeMClauseModal`) close on Escape (added during finish review — the original had click-only dismissal).

## Known deliberate exceptions to the craft floor

- `.cap-grid` (4 icon+heading+text cards on the landing page) reaches for a pattern the floor calls "the lazy container." Judged acceptable here because it's one of five structurally distinct sections on that page (hero, trust card, capability grid, data panels, external links) rather than the page's entire structure, and each card is a real navigation action, not filler.
- `.audit-summary-strip` / `.benchmark-metrics-grid` use a big-number/small-label layout the floor calls the "hero-metric template." Kept because the numbers are real, live audit/evaluation counts central to the product's honesty-layer principle (PRODUCT.md), not marketing stats — flagged by finish review as worth a deliberate look rather than a hard violation.

## Not done this pass

No native/adaptive platform work (web only). No image-generation-based comp existed for this build (code-led, no image tool available this session) — the direction contract's FIRST VIEWPORT block carried the ambition instead, audited against the built screenshots at finish.
