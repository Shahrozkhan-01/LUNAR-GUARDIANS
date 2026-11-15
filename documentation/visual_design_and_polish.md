# Visual Design and Polish

## Design changes

Phase 6 builds on the existing LUNAR GUARDIANS visual system rather than
replacing it. The shared palette now has stronger mission-control depth through
subtle atmospheric gradients, glass-panel hover states, clearer focus/tap
behavior, and consistent cyan/orange status accents.

The landing page keeps its lunar artwork and animated starfield while adding a
lightweight orbital ring motion and a restrained glow on the primary launch
action. The shared background now includes softly animated, CSS-rendered Moon,
Saturn-like, and Mars-like decorative objects and brighter atmospheric color
gradients. The objects are illustrative, not to scale, and are not live solar
system positions. Mission Setup cards now provide stronger selected-state
feedback and panel hover hierarchy. Mission Control panels and resource cards
gain small lift/border transitions, while the final outcome report arrives
with a short success/failure-neutral reveal animation.

No mission configuration, NASA data, resource calculation, event consequence,
or scoring logic was changed.

## Sound implementation

Sound effects use the browser Web Audio API and generated oscillator tones, so
the phase adds no audio files, third-party libraries, or licensing risk. A
single reusable audio context is resumed from the sound-toggle gesture so
browser autoplay policies do not leave later tones suspended.

Supported cues include:

- Hovering an interactive button, link, or card.
- Button interaction.
- Selection and navigation feedback.
- Mission initialization.
- Successful action/day feedback.
- Warning or failed-day feedback.

The sound preference is stored in `localStorage` under
`lunar-guardians-sound-enabled`. Sound is off by default, there is no
autoplay/background music, and unsupported or blocked audio fails silently
without affecting gameplay.

## Accessibility and performance

- Existing semantic buttons, labels, `aria-pressed`, and keyboard focus styles
  were preserved.
- The sound control exposes an accessible label and pressed state.
- `prefers-reduced-motion: reduce` disables non-essential animation and smooth
  scrolling.
- Animations remain CSS/framer-motion based; no heavy dependency was added.
- Background effects are pointer-free and do not intercept gameplay controls.
- Existing responsive breakpoints remain in use and global horizontal overflow
  remains disabled.

## Validation

- Backend: `python -m unittest discover -s tests -v` — **49 tests passed**.
- Frontend lint: `npm run lint` — **passed**.
- Frontend production build: `npm run build` — **passed**.
- Browser smoke checks covered landing page, Mission Setup, Mission Control,
  NASA training cards, sound toggle visibility, mission navigation, and
  responsive layouts at 1366x768, 1024x768, and 390x844.

## Remaining limitations

- Generated tones are intentionally simple and cannot provide the richness of
  recorded sound design.
- Web Audio playback is subject to browser user-gesture and privacy policies.
- The existing Vite bundle-size advisory remains non-blocking.
