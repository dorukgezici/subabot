# Frontend modernization, 11 October 2026

Subabot now uses Astro 7.3.8 and React 19.3.0, with @astrojs/react 7.0.1, @astrojs/node 11.1.7 for standalone builds, and @astrojs/vercel 11.0.12 for hosted builds. Exact versions are resolved in `frontend/package-lock.json`. The supported deployment runtime is Node 24.

The old frontend was Astro 4 with Svelte islands, not a complete SvelteKit app. The rewrite removes Svelte, its integration, Font Awesome, DaisyUI, Tailwind integration, old Astro actions, and the obsolete hybrid/Vercel serverless configuration. Astro renders static marketing pages and dynamic public watchlists. The private inbox is one React island. Plain CSS and locally bundled variable fonts provide the visual system without third-party font requests.

## Changelog decisions

- [Astro 6 migration guide](https://docs.astro.build/en/guides/upgrade-to/v6/) documents the modern Node baseline and changed server APIs. The obsolete hybrid output is replaced with server output and explicit prerendering for the landing and legal pages.
- [Astro 7.3.8 release](https://github.com/withastro/astro/releases/tag/astro%407.3.8) includes Rolldown/Oxc build changes and error-handler fixes. This rebuild uses normal integration APIs, with no custom compiler hooks or old Vite plugins.
- [Astro React integration changelog](https://github.com/withastro/astro/blob/main/packages/integrations/react/CHANGELOG.md) informed the current integration upgrade. The dashboard uses client-only React hydration; the landing demo also renders meaningful static content before hydration.
- [React 19.3 release](https://github.com/react/react/releases/tag/v19.3.0) is the current stable React release checked for this rebuild. The UI uses ordinary hooks, native dialogs and declarative rendering, with cancellable requests for changing filters. No experimental APIs are required.
- TypeScript 7 was available from npm but is outside @astrojs/check 0.9.10's declared peer range. The project deliberately locks compatible TypeScript 6 rather than forcing an unsupported dependency tree.
- Lucide 1.55 no longer exports a GitHub brand icon. Source-code links use the supported Code2 icon.
- The [Vercel adapter changelog](https://github.com/withastro/astro/blob/main/packages/integrations/vercel/CHANGELOG.md) records the build-tool change in 11.0.13. That patch leaked a Rolldown import into the deployed runtime, causing a missing-native-binding startup failure. The project pins 11.0.12 exactly; its generated function passes an isolated bundle check without resolving dependencies from the source checkout.

## Runtime and privacy

The browser talks to a same-origin API route. It forwards only the required browser headers to a fixed backend origin, overwrites trusted client-address and gateway headers, caps streamed request bodies at 32KiB, and gives useful errors when the backend is unavailable. Compose uses private networking. The Vercel-to-k3s deployment additionally authenticates the proxy with a server-only shared secret before the backend trusts its client address.

Workspace access is an opaque capability key in browser local storage. A private recovery file can be exported and used on another device. There is no email signup, password reset, or third-party analytics in this version. A demo workspace is explicitly labeled sample data and never writes to the backend.

Public watchlists require an explicit publish action. Their SSR pages and dynamically rendered PNG social cards recheck publication state and use no-store caching. Unpublishing disables the old page and image. Public rendering escapes user text, and imported article links are restricted to HTTP(S).

Social cards load the bundled OFL-licensed DM Sans font directly with system font discovery disabled. Both deployment targets include the same font. Production and preview builds use the canonical `PUBLIC_SITE_URL`, while exact Vercel deployment hostnames remain valid request hosts.

## Verification

Frontend type checking and production build pass with zero errors, warnings or hints. Browser tests cover API-backed monitor CRUD and persistence, sample inbox filtering, saving and reading, publication/cloning/revocation, social card metadata, workspace recovery, and mobile template discovery. Visual checks cover mobile and desktop, keyboard dialogs, reduced motion, no-JavaScript marketing content, internal links and semantic metadata.
