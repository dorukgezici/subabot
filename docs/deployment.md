# Public deployment

## Current rollout checkpoint

As of the 11 October 2026 preparation checkpoint, the rebuilt production release
has not been cut over. Work is on `codex/public-launch`. Frontend previews and the
immutable backend image are prepared. Operator access through Tailscale has been
restored with approval. A separate approval for the temporary cluster-local legacy
backup Job and its restricted RBAC is pending. Complete that backup before
replacing the old Pod; preparation may be committed without claiming release.
The complete Helm chart has passed a live server dry-run, including the installed
resource schemas. This validation did not apply the chart or establish runtime
readiness.

## Hosting architecture

| Component | Target and configuration |
| --- | --- |
| Frontend | Existing Vercel project `subabot`, DGtech team, canonical `https://subabot.gezici.me` |
| Frontend build | Root `frontend`, Node 24, `npm ci`, `npm run build`, function region `fra1` |
| Backend | Existing k3s infrastructure, HTTPS ingress `https://subabot.pub.gezici.me` |
| Backend delivery | Argo CD Application `argocd/subabot`, destination namespace `default`, repository `dorukgezici/subabot`, path `backend/helm`, normal target `HEAD`, automatic prune and self-heal |
| Persistence | Retained Longhorn PVC `default/subabot-data`, 1 GiB, mounted at `/data` |
| Backend process | One replica, one Uvicorn worker, one scheduler, `Recreate` upgrades |

Vercel builds select their adapter using the automatic `VERCEL=1` environment
variable. Docker and local builds retain standalone Node. Deploy source through
a remote Linux build because resvg has a native dependency. Do not deploy a
macOS prebuilt function bundle.

The Vercel adapter is pinned to `11.0.12`. Version `11.0.13` leaked a Rolldown
import into the runtime and failed cloud startup. The pinned version passes an
isolated function-bundle check. Retest both isolation and hosted startup before
upgrading it. Social images load bundled DM Sans instead of system fonts.

## Immutable backend artifact

The reviewed Linux AMD64/ARM64 artifact is:

```text
docker.io/dorukgezici/subabot:v2-d6a0e28710cabd1fb6bb1c245e6ff935ebea90ba
docker.io/dorukgezici/subabot@sha256:15a3bc34f63b2c0b2dda963f76c664e7516f15d67f507f1a9a402824962bef21
```

The [publication workflow](https://github.com/dorukgezici/subabot/actions/runs/38097644184)
passed. `backend/helm/values.yaml` pins the digest. Future releases can dispatch
`backend-build.yml` with `publish_backend=true`, verify the published digest, and
update the chart. The workflow uses commit-specific tags without replacing the
legacy `latest` image. A later chart/docs-only commit can intentionally reference
an earlier source commit's unchanged backend artifact.

## Configuration and gateway boundary

Vercel production and preview use:

```text
PUBLIC_SITE_URL=https://subabot.gezici.me
BACKEND_URL=https://subabot.pub.gezici.me
```

Set Vercel's server-only `BACKEND_PROXY_SECRET` to the same strong random value as
Kubernetes Secret `default/subabot-proxy`, key `shared-secret`. The chart maps
that key to `SUBABOT_PROXY_SHARED_SECRET`. The chart never creates or embeds the
secret, and imports no legacy `envFrom`. Never put its value in commands that
print it, URLs, source control, logs, browser code, or public environment variables.
Missing and invalid gateway keys return 401 for `/api/*`, except `/api/health`.
Workspace authorization still requires a separate capability bearer token.

The chart also sets the database to `sqlite:////data/subabot.db`, frontend origin
to `https://subabot.gezici.me`, scheduler to enabled with a 900-second interval,
and proxy IP trust to enabled. The frontend overwrites both gateway and client-IP
headers. Secret protection must be active before exposing that trusted backend.

The non-root Pod uses UID/GID/fsGroup 10001, a read-only root filesystem, and a
writable `/tmp`. See [chart documentation](../backend/helm/README.md) for probes,
resources, TLS preservation, and the app-specific Traefik controls. Traefik's
backend response-header timeout is 150 seconds, the frontend scan deadline is
130 seconds, and the Vercel function budget is 180 seconds. Shared ingress or
upstream CDN timeouts are separate and must allow these requests.

## Legacy backup boundary

Preserve the previous image reference and deployment manifests in a secure
operator-controlled location before replacement. Do not rely on a transient
local `/tmp` path as the only rollback record. Manifest records must not contain
secret values.

The legacy chart remains in Git at `44b1eeab4e21d3e3b474f7b8f307bce7c682794b`.
The running legacy Pod's resolved image was
`docker.io/dorukgezici/subabot@sha256:c9e9fc5131e90fd1b70129bedb89cc32d9359872cb49f7d64a652c2d3b88eb24`.
Keep that immutable reference for restoration on the existing cluster rather
than relying on the mutable `latest` tag.

The prepared backup design keeps legacy database bytes inside the cluster. Its
temporary Job uses tightly scoped access to exec only into the exact old Subabot
Pod, takes a SQLite-aware snapshot, and writes
`/data/legacy/database-before-rebuild.sqlite` on the retained PVC. Require a
successful source command and `PRAGMA integrity_check` before accepting the
backup. Use restrictive file permissions and log only status, size, and path.
Remove the temporary Job, ConfigMap, Role, RoleBinding, and ServiceAccount after completion.
Do not run this step before its specific approval is granted.

Do not export the legacy database to the Mac, logs, Git, or another storage
destination under the current rollout boundary. A backup on the same PVC is a
rollback copy, not protection against volume loss. Operators should configure an
appropriate separate disaster-recovery destination and test restoration.

The new application starts a fresh `/data/subabot.db`. The legacy schema is not
compatible and must never be copied over that file. Retention annotations
`Prune=false,Delete=false` and Helm `keep` preserve the PVC during ordinary
application cleanup; they do not prevent direct PVC deletion or hardware loss.

## Staged release order

1. Complete and verify the cluster-local legacy backup, preserve rollback
   manifests/image, and configure matching gateway secrets on both hosts.
2. Validate the exact reviewed chart commit offline:

   ```sh
   helm lint backend/helm --strict
   helm template subabot backend/helm --namespace default > /tmp/subabot-rendered.yaml
   ```

3. Temporarily point the existing Argo application at that exact reviewed commit
   from the release branch. Keep the same repository, chart path, destination,
   and application identity. Record the prior `HEAD` target for restoration.
4. Let Argo reconcile the new chart. `Recreate` stops the old backend before the
   new one starts; there is a short interruption. Verify PVC binding, Pod
   readiness, image digest, gateway rejection, API health, and feed access.
5. Build a refreshed Vercel preview with the matching gateway key. Run the full
   preview smoke below, then check recovery and mobile flows in a browser.
6. Once backend and preview checks pass, merge the reviewed release and restore
   Argo's target to `HEAD`. Coordinate the Vercel production release because Git
   integration may deploy the same merge automatically. Verify the canonical
   production origin and record its deployment ID and source commit.

Do not use a manual `kubectl set image` change as a durable release or rollback:
Argo self-heal will reconcile it against Git. Do not edit other applications or
shared Traefik settings as part of this chart rollout.

## Public smoke checks

Run from the repository root with Node 24. For a preview whose canonical metadata
points to the production origin:

```sh
SUBABOT_CHECK_CANONICAL_ORIGIN=https://subabot.gezici.me \
  node scripts/verify-deployment.mjs https://YOUR_PREVIEW_HOST.vercel.app
```

After production release:

```sh
node scripts/verify-deployment.mjs https://subabot.gezici.me
```

The script creates two disposable workspaces, ingests real RSS, verifies saved
state/search, checks workspace isolation, briefly publishes a watchlist, checks
its page/PNG and clone settings, revokes it, and deletes its workspaces. It never
connects Slack or prints recovery keys. A nonzero exit means the release check
failed, including cleanup failure. Check its help before changing the target:

```sh
node scripts/verify-deployment.mjs --help
```

Also verify `/robots.txt`, `/sitemap.xml`, dashboard GET/HEAD, HTTPS, runtime logs,
and recovery import/export through the real browser. Slack remains unverified
until a separately configured real webhook is tested.

## Rollback

For a compatible new-schema release, target a previously verified chart commit
or revert the immutable image digest in Git, then let Argo reconcile it. Keep the
same PVC and one replica. Promote the matching previous Vercel production
deployment, preserving compatible gateway settings. Restore Argo's normal `HEAD`
tracking once the corrective commit is on the tracked branch.

Returning to the legacy application is a different recovery operation. Its old
image expects its own schema and storage path. Use the preserved manifests and
verified in-cluster legacy snapshot, while preserving the new database
separately. Do not overwrite either schema, delete the retained PVC, or assume
an image rollback migrates data. Coordinate this database recovery with rolling
the frontend back to its corresponding release.
