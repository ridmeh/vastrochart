# <= 50 chars, alnum + hyphens, globally unique (forms the *.azure-api.net
# hostname).
resource "azurerm_api_management" "this" {
  name                = "apim-${var.project}-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  publisher_name      = var.apim_publisher_name
  publisher_email     = var.apim_publisher_email
  sku_name            = "Consumption_0"
  tags                = local.tags
}

# Fetched live from the running Container App (not a checked-in static
# file) so the imported contract can never drift from the real app -
# FastAPI already generates this for free from the same Pydantic models
# the app actually validates against. Downgraded from the generated
# OpenAPI 3.1.0 to 3.0.3 by scripts/convert_openapi_30.py - verified
# empirically that APIM's 3.1 import validator rejects valid 3.1
# JSON-Schema constructs FastAPI emits (exclusiveMinimum as a number,
# Optional[T] as anyOf-with-null); see that script's docstring and
# docs/05-decisions.md ADR-041.
data "external" "openapi_spec_30" {
  program = ["python3", "${path.module}/scripts/convert_openapi_30.py"]
  query = {
    url = "https://${azurerm_container_app.this.ingress[0].fqdn}/openapi.json"
  }

  depends_on = [azurerm_container_app.this]
}

locals {
  openapi_raw = jsondecode(data.external.openapi_spec_30.result.spec)

  # /healthz and /readyz are split into their own unauthenticated API
  # below (azurerm_api_management_api.health) rather than living here -
  # the real compute endpoints all need a subscription key, but a health
  # probe (Front Door's own, or anyone else's) must not have to carry one.
  openapi_compute_only = jsonencode(merge(local.openapi_raw, {
    paths = {
      for path, ops in local.openapi_raw.paths : path => ops
      if !contains(["/healthz", "/readyz"], path)
    }
  }))

  openapi_health_only = jsonencode(merge(local.openapi_raw, {
    paths = {
      for path, ops in local.openapi_raw.paths : path => ops
      if contains(["/healthz", "/readyz"], path)
    }
  }))

  backend_url = "https://${azurerm_container_app.this.ingress[0].fqdn}"
}

resource "azurerm_api_management_api" "compute" {
  name                  = "vastrochart-compute"
  resource_group_name   = azurerm_resource_group.this.name
  api_management_name   = azurerm_api_management.this.name
  revision              = "1"
  display_name          = "VAstroChart Compute"
  path                  = ""
  protocols             = ["https"]
  service_url           = local.backend_url
  subscription_required = true

  import {
    content_format = "openapi+json"
    content_value  = local.openapi_compute_only
  }

  # Forces this to wait for health's path to actually change away from ""
  # first - without this, Terraform applies both in parallel (no implicit
  # dependency between them) and this import can transiently collide with
  # health's old path="" mid-transition. Found empirically: the exact same
  # import content succeeded standalone once health was already at "ops".
  depends_on = [azurerm_api_management_api.health]
}

# subscription_required = false is what actually matters - that's the
# setting that exempts these two paths from needing a key, independent
# of which products exist or what they require. path = "ops" (not "") is
# required too: APIM rejects two separate API entities that share the
# same path+protocol+type ("unless it's a part of the same version set",
# found empirically) - compute already owns path "", so health's
# operations land at /ops/healthz and /ops/readyz instead of bare
# /healthz/readyz (Front Door's health_probe path is adjusted to match).
resource "azurerm_api_management_api" "health" {
  name                  = "vastrochart-health"
  resource_group_name   = azurerm_resource_group.this.name
  api_management_name   = azurerm_api_management.this.name
  revision              = "1"
  display_name          = "VAstroChart Health"
  path                  = "ops"
  protocols             = ["https"]
  service_url           = local.backend_url
  subscription_required = false

  import {
    content_format = "openapi+json"
    content_value  = local.openapi_health_only
  }
}

# Free/Starter/Pro/Scale tiers per docs/03-architecture.md's rate-limit
# table (1k/50k/500k/5M calls/mo). quota's renewal_period is a rolling
# window in seconds, not a calendar-month reset - 2,592,000s (30 days) is
# the standard approximation, not a true billing-month quota. Per-minute
# rate_limit figures aren't specified in that doc (only the monthly
# figures are) - these are reasonable defaults to stop burst abuse, not
# values derived from a committed spec; revisit once real traffic
# patterns exist.
locals {
  tiers = {
    free = {
      display_name = "Free"
      description  = "Evaluation tier - 1,000 calls/month."
      quota_calls  = 1000
      rate_limit   = 10
    }
    starter = {
      display_name = "Starter"
      description  = "50,000 calls/month."
      quota_calls  = 50000
      rate_limit   = 60
    }
    pro = {
      display_name = "Pro"
      description  = "500,000 calls/month."
      quota_calls  = 500000
      rate_limit   = 300
    }
    scale = {
      display_name = "Scale"
      description  = "5,000,000 calls/month."
      quota_calls  = 5000000
      rate_limit   = 1200
    }
  }
}

resource "azurerm_api_management_product" "tier" {
  for_each = local.tiers

  product_id            = each.key
  resource_group_name   = azurerm_resource_group.this.name
  api_management_name   = azurerm_api_management.this.name
  display_name          = each.value.display_name
  description           = each.value.description
  subscription_required = true
  # Auto-approved for now - every tier is self-serve until Stripe billing
  # exists (docs/06-roadmap.md); gating approval on successful payment is
  # a Stripe-wiring concern, not an API Management one, so revisit this
  # flag when that lands, not before.
  approval_required   = false
  published           = true
  subscriptions_limit = 1
}

resource "azurerm_api_management_product_api" "tier" {
  for_each = local.tiers

  product_id          = azurerm_api_management_product.tier[each.key].product_id
  api_name            = azurerm_api_management_api.compute.name
  resource_group_name = azurerm_resource_group.this.name
  api_management_name = azurerm_api_management.this.name
}

resource "azurerm_api_management_product_policy" "tier" {
  for_each = local.tiers

  product_id          = azurerm_api_management_product.tier[each.key].product_id
  resource_group_name = azurerm_resource_group.this.name
  api_management_name = azurerm_api_management.this.name

  # The *-by-key variants (custom counter-key expressions) aren't allowed
  # on the Consumption SKU - verified empirically ("Policy is not allowed
  # in 'Consumption' sku"). The plain rate-limit/quota policies are
  # Consumption-compatible and scope per-subscription by default anyway,
  # which is exactly the per-API-key behavior each tier needs.
  xml_content = <<XML
<policies>
  <inbound>
    <base />
    <rate-limit calls="${each.value.rate_limit}" renewal-period="60" />
    <quota calls="${each.value.quota_calls}" renewal-period="2592000" />
  </inbound>
</policies>
XML
}
