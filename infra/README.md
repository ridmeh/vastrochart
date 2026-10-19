# VAstroChart Infra

Terraform for the Week 3 deploy target (`docs/06-roadmap.md`, `docs/03-architecture.md`): Resource Group, ACR, Log Analytics + App Insights, Key Vault, ACA Environment + Container App, Front Door Premium (+ WAF), API Management (Consumption).

**Status: the real image is live**, CI/CD is wired (`.github/workflows/deploy.yml` - push to `main` → test → `az acr build` → `az containerapp update`), and the request path is `Client → Front Door (WAF) → API Management (key + rate limit) → Container App` end to end, matching `docs/03-architecture.md`.

## What this does NOT do yet

- Create any Key Vault secret values (Stripe webhook secret, API-key pepper) - those don't exist yet
- Point a real DNS name (`api.vastrochart.com`) at the Front Door endpoint - you don't own that domain in this environment yet
- Stripe wiring
- **A non-prod environment.** `deploy.yml` currently builds and deploys straight to this one environment (`vac-prod`) on every push to `main` - intentionally, per the owner (2026-10-19): prove the build/deploy/test flow against prod first, *then* split into a non-prod path that gets tested before promoting the same image to prod. Not yet started. Don't assume the direct-to-prod pipeline is the final design when touching this again.

The Container App starts out running a public placeholder image (`mcr.microsoft.com/azuredocs/containerapps-helloworld`, listens on port 80 - verified by running it locally) so `apply` succeeds with nothing in ACR yet, and deliberately has no `registry` block or health probes wired in yet either (see the comments in `container_apps.tf` - a first apply with those in place hung for 20+ minutes and failed with "Operation expired", because the placeholder serves neither `/healthz` nor `/readyz` and AcrPull can't exist before the container app's identity does).

Once the real image is pushed to ACR, in one apply:
1. Set `container_image` to `<acr_login_server>/vastrochart-compute:<tag>`
2. Set `container_target_port` to `8080` (the real image's Dockerfile EXPOSEs that port, not the placeholder's 80)
3. Uncomment the `registry` block and the two probe blocks in `container_apps.tf`
4. `terraform apply`

## Running it

```bash
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars: subscription_id, apim_publisher_email

terraform init
terraform plan
terraform apply
```

State is local (`terraform.tfstate`, gitignored) - fine solo, move to a remote backend before anyone else touches this.

## After apply

```bash
terraform output container_registry_login_server   # push your image here
terraform output front_door_endpoint_hostname       # public, WAF-protected URL
terraform output container_app_fqdn                 # direct ACA URL, bypasses Front Door - debugging only
```

## CI/CD identity (NOT in Terraform - set up imperatively via az/gh CLI)

GitHub Actions authenticates to Azure via OIDC (no stored client secret): an Azure AD app (`github-actions-vastrochart`, app ID in GitHub secret `AZURE_CLIENT_ID`) with a federated credential trusting this repo/branch, scoped to roles on exactly two resources - the ACR and the Container App - nothing broader. GitHub repo secrets hold the three OIDC identifiers (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`); repo variables hold the non-sensitive resource names (`ACR_NAME`, `ACR_LOGIN_SERVER`, `RESOURCE_GROUP`, `CONTAINER_APP_NAME`).

Two things found empirically, not from documentation, while getting the first real deploy to go green:
- **The federated credential's `subject` is not the plain `repo:OWNER/REPO:ref:refs/heads/BRANCH` form the standard docs describe.** The token this specific repo/account actually presents is `repo:ridmeh@17874565/vastrochart@1414080279:ref:refs/heads/main` (numeric IDs appended after `@`) - found from the exact string Azure AD's `AADSTS700213` rejection error echoed back, not guessed. If this ever needs recreating, read the real subject off a failed run's error rather than assuming the textbook format.
- **`AcrPush` alone isn't enough for `az acr build`.** It let the identity push/pull images but not resolve/run against the registry via `az acr build` (`ERROR: The resource ... could not be found`, even though it demonstrably exists) - `az acr build` goes through ACR Tasks, which needs more than the data-plane push/pull role. Widened to `Contributor` scoped to just that one ACR resource (still not subscription- or RG-wide).

This isn't Terraform-managed yet - it was faster to stand up via `az ad app create` / `az ad app federated-credential create` / `az role assignment create` / `gh secret set` / `gh variable set` directly. Codifying it with the `azuread` provider (plus `terraform import` for the resources that already exist) would close that gap if this ever needs to be reproducible from scratch rather than just re-run.

## API Management (Step 3 - products, tiers, rate limits)

`api_management.tf` imports the app's own OpenAPI spec (fetched live from the running Container App, not a checked-in file - see `scripts/convert_openapi_30.py`'s docstring) as two separate API entities:
- `vastrochart-compute` (path `""`, the real `/v1/*` endpoints) - `subscription_required = true`
- `vastrochart-health` (path `"ops"`, `/healthz` + `/readyz` only) - `subscription_required = false`, so a health probe never needs a key. Reachable at `/ops/healthz` / `/ops/readyz` through the gateway - not the bare paths, which only exist on the Container App directly.

Four products (Free/Starter/Pro/Scale) each get the compute API plus a `rate-limit`/`quota` policy matching `docs/03-architecture.md`'s 1k/50k/500k/5M-calls/month table. Every tier auto-approves subscriptions for now (no Stripe gate yet - see `api_management.tf`'s comments).

Three things found only by actually running this, not from documentation:
- **Azure API Management's OpenAPI 3.1 import validator is incomplete.** It rejects valid JSON-Schema-2020-12 constructs FastAPI emits by default (`exclusiveMinimum` as a number instead of 3.0's boolean+`minimum` pair; `Optional[T]` as `anyOf: [T, {"type": "null"}]` instead of 3.0's `nullable: true`) with an opaque `ValidationError: One or more fields contain incorrect values` - no detail unless you go around Terraform and try the same content via `az apim api import` directly, which does print the real cause. `scripts/convert_openapi_30.py` downgrades the fetched 3.1 spec to 3.0.3 before import.
- **The Consumption SKU doesn't support `rate-limit-by-key`/`quota-by-key`** ("Policy is not allowed in 'Consumption' sku") - only the plain `rate-limit`/`quota` policies, which happen to be exactly right anyway since they scope per-subscription by default.
- **Two API entities can't share the same `path` + protocol + type** ("unless it's a part of the same version set") - the health API needed its own `path = "ops"`, not `""`, once `compute` also claimed `""`. Changing that path on an existing API, in the same apply as creating `compute` for the first time, hit a second issue: Terraform parallelizes independent resources by default, and `compute`'s creation raced `health`'s path change - fixed with an explicit `depends_on`.
