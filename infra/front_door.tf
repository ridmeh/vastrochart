resource "azurerm_cdn_frontdoor_profile" "this" {
  name                = "afd-${local.name_prefix}"
  resource_group_name = azurerm_resource_group.this.name
  sku_name            = "Premium_AzureFrontDoor"
  tags                = local.tags
}

# <= 46 chars, alnum + hyphens, globally unique (forms the *.azurefd.net hostname).
resource "azurerm_cdn_frontdoor_endpoint" "this" {
  name                     = "${var.project}-${random_string.suffix.result}"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id
  tags                     = local.tags
}

resource "azurerm_cdn_frontdoor_origin_group" "this" {
  name                     = "og-compute"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id

  load_balancing {}

  health_probe {
    protocol = "Https"
    # /ops/healthz, not bare /healthz - the origin is now API Management
    # (see azurerm_cdn_frontdoor_origin.this below), and its unauthenticated
    # health API is mounted at the "ops" path prefix (api_management.tf).
    path                = "/ops/healthz"
    request_type        = "GET"
    interval_in_seconds = 30
  }
}

locals {
  apim_hostname = replace(azurerm_api_management.this.gateway_url, "https://", "")
}

# Public entry point is API Management, not the Container App directly -
# matches docs/03-architecture.md's Front Door -> API Mgmt -> Container
# Apps chain. Bypassing APIM here would mean the subscription keys and
# rate limits configured in api_management.tf never actually apply to
# real traffic - API Management has to sit in the path, not beside it.
resource "azurerm_cdn_frontdoor_origin" "this" {
  name                          = "origin-compute"
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.this.id

  enabled                        = true
  host_name                      = local.apim_hostname
  origin_host_header             = local.apim_hostname
  https_port                     = 443
  certificate_name_check_enabled = true
}

resource "azurerm_cdn_frontdoor_route" "this" {
  name                          = "route-compute"
  cdn_frontdoor_endpoint_id     = azurerm_cdn_frontdoor_endpoint.this.id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.this.id
  cdn_frontdoor_origin_ids      = [azurerm_cdn_frontdoor_origin.this.id]

  supported_protocols    = ["Http", "Https"]
  patterns_to_match      = ["/*"]
  forwarding_protocol    = "HttpsOnly"
  https_redirect_enabled = true
  link_to_default_domain = true
}

# WAF policy name must be alnum-only (Azure naming rule for this resource type).
# Managed-rule-set version below is current as of this session but Azure
# revises these periodically - verify against `az network front-door waf-policy
# managed-rule-definition list` before relying on this if it's been a while.
resource "azurerm_cdn_frontdoor_firewall_policy" "this" {
  name                = "waf${replace(local.name_prefix, "-", "")}"
  resource_group_name = azurerm_resource_group.this.name
  sku_name            = azurerm_cdn_frontdoor_profile.this.sku_name
  mode                = "Prevention"

  managed_rule {
    type    = "Microsoft_DefaultRuleSet"
    version = "2.1"
    action  = "Block"
  }

  tags = local.tags
}

resource "azurerm_cdn_frontdoor_security_policy" "this" {
  name                     = "secpol-${local.name_prefix}"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id

  security_policies {
    firewall {
      cdn_frontdoor_firewall_policy_id = azurerm_cdn_frontdoor_firewall_policy.this.id

      association {
        domain {
          cdn_frontdoor_domain_id = azurerm_cdn_frontdoor_endpoint.this.id
        }
        patterns_to_match = ["/*"]
      }
    }
  }
}
