---
name: design-system
description: Use this skill whenever writing, editing, or reviewing ANY frontend UI in this project — pages, components, CSS/Tailwind config, or copy layout. Defines Hear-Me's visual language (colors, type, spacing, components) and an explicit list of forbidden patterns. Do not invent colors, gradients, shadows, or component styles outside what's defined here.
---

# Hear-Me Design System — "Midnight Editorial"

Blend of two reference systems: **Endlesstools** (near-black canvas, hairline-border
elevation, disciplined restrained color) + **Cora** (light-serif display type paired
with a neutral sans, editorial/premium tone). Applied here to a dark canvas because
Hear-Me's own content (album art, playlist covers) needs to be the most colorful thing
on screen — the UI stays quiet so the music's artwork can carry the color.

## Forbidden patterns (explicit — these are what "AI slop" looks like here)

Do NOT use any of the following, even if it seems like a reasonable default:

- Linear-gradient text fill (`background-clip: text` with a color gradient)
- Multi-color gradients on buttons, borders, or backgrounds of any kind
- Glow / blur box-shadows (e.g. `shadow-[0_0_36px_...]`, colored blurred shadows behind buttons)
- Decorative radial "glow" background blobs behind hero sections
- Decorative grid-line background patterns with no functional purpose
- Pill badges with a colored dot + uppercase micro-label used purely as decoration
  (e.g. "● Playlist sync · Auto-sort · Discovery")
- Rounded-full (9999px) buttons as the DEFAULT for every button — reserve full-pill
  radius for tags only (see Radius below)
- More than ONE chromatic accent color anywhere on a single screen
- Drop shadows for elevation — elevation is drawn with a 1px hairline border, never a shadow

If you're about to write a class name containing "glow", "gradient-text", or a radial
background-image for decoration only — stop, that's the pattern this skill exists to prevent.

## Color tokens

Replace ALL existing tokens in `frontend/app/globals.css` with these:

```css
--color-canvas: #0a0a0c;       /* page background */
--color-surface: #17171a;      /* card fills */
--color-surface-2: #1e1e22;    /* input backgrounds, subtle lift */
--color-border: #2b2b30;       /* primary 1px hairline border */
--color-border-strong: #444448;/* emphasis border */
--color-ink: #f2f2f0;          /* primary text */
--color-muted: #8f8f96;        /* secondary text, placeholders */
--color-accent: #d9a441;       /* single chromatic accent — "vinyl gold". Used for
                                   primary CTA fill, links, and active states ONLY */
--color-danger: #e5484d;
```

Only `--color-accent` is chromatic. Everything else is neutral. Do not add a second
brand color, and do not use `--color-accent` for more than one element type per screen
(e.g. if it's the primary button, it should NOT also be the link color on the same view).

## Typography

Two type families, strict role separation:

- **Display / headlines** (h1, hero text, section titles ≥28px): a light-weight serif.
  `font-family: "Fraunces", "Cormorant Garamond", Georgia, serif;` weight 300-400 only.
  Never use the serif for body text, buttons, nav, or labels.
- **UI / body** (everything else — nav, buttons, body copy, forms, labels): Inter,
  weight 400 (body) or 500 (emphasis/nav) only. Never bold (700) for headings — let
  size and the serif pairing carry hierarchy, not font-weight.

## Spacing & Shape

- Border radius: **10px** for cards, inputs, and buttons (default). **9999px (pill)**
  reserved exclusively for small tag/category chips — not for primary buttons.
- Elevation: 1px solid `--color-border` only. No box-shadow anywhere except
  `focus-visible` outlines.
- Section gap: 80-100px between major page sections. Card padding: 20-24px.

## Component patterns

- **Primary button**: solid `--color-accent` fill, `--color-canvas` text, 10px radius,
  no shadow, no gradient. This is the ONLY filled-color element that should appear per view.
- **Secondary button**: transparent fill, 1px `--color-border` outline, `--color-ink`
  text, 10px radius.
- **Card**: `--color-surface` fill, 1px `--color-border`, 10px radius, no shadow.
- **Input**: `--color-surface-2` fill, 1px `--color-border`, 10px radius, focus state
  changes border to `--color-border-strong` (not a colored ring/glow).
- **Hero section**: serif headline directly on `--color-canvas`, no decorative
  background image/gradient/grid behind it. If album art or user content is available,
  that can be the visual anchor — not an abstract gradient blob.

## Checklist before considering any frontend page "done"

- [ ] No gradient text, no glow shadow, no decorative grid/radial background
- [ ] Exactly one chromatic accent color used, and only for one element role
- [ ] Serif used only on headline-level text, sans everywhere else
- [ ] Elevation is hairline border, not shadow
- [ ] Buttons are 10px radius, not pill, unless it's a small tag chip
