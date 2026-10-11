# Subabot design direction

## Product and funnel brief

Subabot watches public RSS and Atom feeds for keyword matches, collects the matching items in an inbox, and can send them to a Slack incoming webhook. It is for independent builders, researchers, and small teams who need to follow a specific topic without another reading backlog.

The promise is specific: choose the sources and words that matter, then receive matching updates. The implementation does not use an AI model and does not monitor every website or the entire internet.

The primary action is **Create your first monitor** at `/dashboard`. The secondary action is **Explore the demo** at `/dashboard?demo=1`. A public starter library at `/explore` is the useful, shareable acquisition surface. No signup wall or checkout is implied by the landing copy.

Available evidence: source code, a working product, original RSS monitoring concept, and the named creator Doruk Gezici. There are no customer logos, testimonials, or usage metrics to display. All illustrative results must carry a sample-data label.

Tone: calm, precise, useful, a little playful. Never claim that a monitor provides exhaustive coverage or instant delivery.

## Primary reference research

Reviewed 11 October 2026. These are structural references, not artwork or copy to reproduce.

- [Linear](https://linear.app/): explains its category before showing a dense, legible product surface. Borrow the tight display typography, strong hierarchy inside the product preview, and progression from outcome to mechanism. Avoid borrowing the dark aesthetic or its customer claims.
- [Readwise Reader](https://readwise.io/read): gives the reader a clear before-and-after, with the product inbox carrying the promise. Borrow recognizable content rows and a reading-oriented, low-friction visual experience.
- [Raycast](https://www.raycast.com/): makes the core interaction visible and gives extensions their own acquisition path. Borrow the idea of an interactive sample and a useful public template library; keep the interaction limited to keyword filtering.
- [Feedly](https://feedly.com/): frames monitoring as collection followed by delivery, with use cases presented as concrete workflows. Borrow that straightforward explanation while keeping Subabot's scope visibly narrower and understandable.

## Directions considered

1. **Quiet signal, selected.** Warm off-white canvas, leafy green emphasis, dark ink typography, generous editorial spacing. A working keyword filter sits inside a realistic, explicitly labeled product illustration. Fits the promise of less noise and feels approachable to solo builders.
2. **Research notebook.** Paper white, serif headings, marginal notes, yellow highlights. Strong editorial character, but too close to a read-it-later tool and less connected to automated Slack delivery.
3. **Control room.** Dense dark interface, monospace labels, status indicators. Communicates technical capability but makes a simple personal workflow feel operationally heavy.

## Visual contract

- Canvas `#f7f8fa`, ink `#17211e`, primary green `#357a57`, pale sage surfaces.
- Manrope display headings, DM Sans body text, local font files supplied by the shared layout.
- Square green bot mark with two white eyes. No robot illustration, gradients, neon, or decorative charts.
- Hero headline approximately 80px on desktop, 48px on mobile. Body text 17-19px. Comfortable content measure and strong contrast.
- A single large product preview earns the visual emphasis. Sample keyword chips actually change the visible sample signals. Automatic cycling stops after one short demonstration, and respects reduced motion.
- Section rhythm: open hero, compact source compatibility strip, white process section, sage template block, ink creator statement, plain FAQ, focused closing paths.
- Buttons have descriptive text, visible focus, and generous hit areas. Mobile navigation retains every desktop destination through a native disclosure.
- Exactly one h1 per page. Semantic landmarks, FAQ disclosures, valid structured data, honest page descriptions, and share image.

## Copy document, agreed before implementation

**Navigation:** How it works / Templates / GitHub / Open app.

**Eyebrow:** A little bot. A lot less noise.

**Hero:** The internet is loud. Find your signal.

**Supporting copy:** Follow the topics you care about, without following everything. Subabot watches your RSS feeds, finds your keywords, and brings the right updates to your inbox and Slack.

**Primary:** Create your first monitor.

**Secondary:** Explore the demo.

**Reassurance:** Open source. No account needed to get started.

**Demo:** Your corner of the internet. Sample data / Your keywords / Signals / Slack preview. Try a keyword to see the inbox change.

**Compatibility:** If it has a public feed, it can be a source. Blogs / News / Changelogs / Communities.

**Mechanism:** A small setup. A quieter day. 01 Pick your sources. 02 Tell it what matters. 03 Catch the useful things.

**Template acquisition:** Good monitors are worth sharing. Start with a focused template. Make it yours. Share the setup when it is useful to someone else.

**Trust:** Small by design. Open by default. An independent project by Doruk Gezici, built around a simple idea: your attention is worth protecting. Inspect the code, suggest a source, or build something on top.

**FAQ:** What can I monitor? / How do keywords work? / Do I need a Slack account? / Does it use AI? / What does it cost? / Can other people see my monitors?

**Close, primary path:** Make room for the things that matter. Start with one feed and one keyword. Create your first monitor.

**Close, secondary path:** Just looking around? Open a sample workspace to see how it feels. Explore the demo.

## Verification expectations

Check at 375px and 1440px widths. Confirm no horizontal overflow, full mobile nav parity, keyboard focus, readable reduced-motion/no-JavaScript rendering, correct CTA URLs, meaningful interactive demo filtering, one h1, valid JSON-LD, and real footer links. Never describe planned growth work as already implemented.

## Verification performed

Browser checks on 11 October 2026 against the local development server:

- Viewed the full page at 1440px and 375px, plus the desktop hero and mobile section detail at native resolution.
- No horizontal overflow at 320, 375, 768, 1280, or 1440px.
- Both keyword choices tested changed the sample article list and Slack preview state; no page errors were reported.
- Mobile disclosure retained all four navigation destinations. FAQ disclosure opened correctly. The first keyboard focus landed on the working skip link.
- With JavaScript disabled, the headline, three sample stories, navigation, and real links remained present. Reduced motion produced zero active animations.
- The landing document has one h1, a 42-character title, a 154-character description, valid JSON-LD, and valid local anchor targets.
- Privacy and terms each have one h1 and no mobile overflow. Both legal pages, the template library, and sample dashboard returned HTTP 200.
- The generated 1200 × 630 PNG share image was visually inspected.

The Astro development toolbar adds its own headings inside a shadow root during development. Checks count the page document, not those development-only controls.

## Final readability pass

The final landing page was checked using computed foreground/background colors for visible text against its flat page surfaces. Secondary text and sample UI labels were darkened; the final pass reported no text below a 4.5:1 contrast ratio. This is a targeted readability check, not a claim of a complete accessibility certification.

An independent dashboard pass also checked the sample and empty workspace. Visible buttons had accessible names, monitor form inputs had labels, and the native modal closed with Escape. The mobile drawer now receives focus, keeps keyboard navigation within its controls, closes with Escape, and restores focus to its opener. The empty workspace shows zero counts and a clear starter-template action.

Final visual evidence is saved in `docs/screenshots/`: desktop and mobile dashboard views, the empty workspace, full landing pages, and hero-only landing images. Screenshots use sample data or a new empty local workspace, with the Astro developer toolbar removed.
