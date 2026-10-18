# VAstroChart Infra

Terraform for the Week 3 deploy target (`docs/06-roadmap.md`, `docs/03-architecture.md`): Resource Group, ACR, Log Analytics + App Insights, Key Vault, ACA Environment + Container App, Front Door Premium (+ WAF), API Management (Consumption).

## What this does NOT do yet

- Push a real image to ACR, or wire CI (GitHub Actions task, separate roadmap line)
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
