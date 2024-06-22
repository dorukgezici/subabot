/// <reference types="astro/client" />
/// <reference path="../.astro/actions.d.ts" />

interface ImportMetaEnv {
  readonly XATA_API_KEY: string;
  readonly XATA_BRANCH?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
