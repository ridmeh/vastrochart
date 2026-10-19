# VAstroChart Infra

Terraform for the Week 3 deploy target (`docs/06-roadmap.md`, `docs/03-architecture.md`): Resource Group, ACR, Log Analytics + App Insights, Key Vault, ACA Environment + Container App, Front Door Premium (+ WAF), API Management (Consumption).

**Status: the real image is live** (`acrvastrochart8oh5a.azurecr.io/vastrochart-compute:v1`, deployed) and CI/CD is wired (`.github/workflows/deploy.yml` - push to `main` → test → `az acr build` → `az containerapp update`).

## What this does NOT do yet

- Import the OpenAPI spec / configure API Management products, key tiers, rate limits (separate roadmap line)
- Create any Key Vault secret values (Stripe webhook secret, API-key pepper) - those don't exist yet
- Point a real DNS name (`api.vastrochart.com`) at the Front Door endpoint - you don't own that domain in this environment yet
- Stripe wiring

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
