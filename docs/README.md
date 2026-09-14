# syllogi docs

Documentation site for [syllogi](https://github.com/jeraldlyh/syllogi), live at **[docs.syllogi.dev](https://docs.syllogi.dev)**.

Built with [Fumadocs](https://fumadocs.dev) on Next.js, exported as a static site (`output: 'export'`), so the build output in `out/` can be served by any static host.

## Development

```bash
pnpm install
pnpm dev           # http://localhost:3000
pnpm build         # static export to out/
pnpm start         # serve out/ locally
pnpm types:check   # typegen + tsc --noEmit
```

## Structure

```
content/docs/          MDX pages, one folder per section
├── index.mdx          overview + credits
├── quick-start.mdx
├── features/          one page per feature
├── configuration/     env vars, Authentik SSO
└── meta.json          sidebar order
app/                   routes, layouts, OG images, llms.txt
lib/shared.ts          site name, GitHub repo, route prefixes
public/assets/         screenshots and icon (copied from ../assets)
```
