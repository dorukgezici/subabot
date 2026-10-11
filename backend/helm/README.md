# Subabot production chart

This chart is the source for the existing Argo CD `argocd/subabot` application,
which tracks `backend/helm` on repository HEAD with automatic prune and self-heal.
Its destination namespace is `default`.
Review the rendered change before merging to the tracked branch. The chart does
not create an Argo application or change shared Traefik configuration.
The initial staged rollout temporarily targets an exact reviewed release-branch
commit, verifies the backend and Vercel preview, then restores `HEAD` after the
reviewed merge. See the [deployment runbook](../../docs/deployment.md) for current
status and backup/rollback records.

The Deployment, Service and Ingress retain the name `subabot` and the existing
`app.kubernetes.io/name=subabot`, `app.kubernetes.io/instance=subabot` selectors.
The Service keeps port 8000. The chart is specific to this installation and uses
fixed names so it can safely replace the old release resources.

## Required existing resources

- Namespace `default` with the existing `traefik` ingress class and Traefik 2.11
  CRDs in `traefik.io/v1alpha1`.
- cert-manager ClusterIssuer `cloudflare` and existing TLS Secret `subabot-tls`
  for `subabot.pub.gezici.me`. This chart references those resources.
- Longhorn StorageClass `longhorn`.
- Secret `subabot-proxy`, key `shared-secret`, containing a nonempty gateway key.
  Its value must match Vercel's server-only `BACKEND_PROXY_SECRET`. The chart
  deliberately does not create or embed that Secret and imports no legacy env.
  Restart the Pod after rotating this environment-backed key.

## Runtime and storage

The immutable image digest is pinned in `values.yaml`. One replica and the
`Recreate` strategy keep one scheduler active and avoid concurrent SQLite
writers across replacement Pods. Upgrades cause a short interruption.

The new 1 GiB `subabot-data` PVC stores `/data/subabot.db`. The backend creates a
fresh database; this chart does not import or alter the old application's data.
Back up the existing application database before replacing its Pod.
The initial legacy snapshot remains inside the cluster at
`/data/legacy/database-before-rebuild.sqlite`. The 45,056-byte backup passed
integrity and restore verification before the initial rollout. It is not an
input migration for the new schema.
The PVC has Argo `Prune=false,Delete=false` and Helm `keep` annotations. Those
protect it from ordinary application cleanup, not manual PVC deletion or disk
failure. Configure database-consistent backups and monitor disk use separately.
Storage grows as matches accumulate; no automatic signal retention is enabled.
Retain the previous image reference and manifests securely for rollback. Argo
self-heal overrides manual image edits, so coordinate rollback through a reviewed
Git revision. Legacy restoration requires its separate schema and storage path.

The Pod runs as UID/GID/fsGroup 10001 with a read-only root filesystem, all
capabilities dropped, no privilege escalation, no service-account token, and a
64 MiB writable `/tmp`. It explicitly uses ServiceAccount `default` with token
automount disabled, preventing inheritance of the removed legacy account.
SQLite writes only under `/data`.
Startup, readiness and liveness probes use unauthenticated `/api/health`.
The health endpoint confirms the API is running, not that any RSS source or
Slack webhook is reachable.

## Subabot ingress controls

The Service selects the namespaced `subabot` ServersTransport with a 150-second
response-header timeout. The Ingress retains TLS on `websecure` and applies two
optional Subabot-only middlewares: a 32 KiB request body cap and a rate limit of
60 requests/second with burst 120. Rate limiting uses Traefik's default remote
address, so requests behind the same Vercel or upstream proxy can share a bucket.
It does not trust arbitrary forwarded-IP headers. Backend workspace limits use
the authenticated frontend's independently supplied client address.

These resources do not override shared entrypoint read/write timeouts or any
upstream CDN timeouts. Confirm those boundaries allow the frontend's 130-second
scan deadline. HTTP is not exposed by this Ingress; use the existing platform
HTTPS redirect if required.

## Offline validation

```sh
helm lint backend/helm --strict
helm template subabot backend/helm --namespace default > /tmp/subabot-rendered.yaml
helm template subabot backend/helm --namespace default \
  --set traefik.buffering.enabled=false \
  --set traefik.rateLimit.enabled=false > /tmp/subabot-minimal-rendered.yaml
```

Rendering and linting validate chart structure without connecting to the cluster.
They do not confirm StorageClass provisioning, installed CRD schema compatibility,
filesystem permissions, image startup, certificate readiness, or external feeds.
Validate those during the controlled rollout before routing public frontend use.
On 11 October 2026, the complete chart passed a live server dry-run, then the
staged deployment at `1d0c16841ef8870c5c791678023b6e77cd8393bf` reached Argo
`Synced` and `Healthy`. The backend Pod was 1/1 Ready with zero restarts, and the
hosted frontend preview passed real-feed and sharing smoke checks. The production
frontend subsequently launched and passed the same smoke at
`https://subabot.gezici.me`; exact release identifiers are in the deployment runbook.

References: [Traefik Service annotations](https://doc.traefik.io/traefik/v2.11/routing/providers/kubernetes-ingress/#on-service),
[ServersTransport](https://doc.traefik.io/traefik/v2.11/routing/services/#serverstransport_1),
[rate-limit sources](https://doc.traefik.io/traefik/v2.11/middlewares/http/ratelimit/#sourcecriterion),
and [Argo CD retention](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-options/).
