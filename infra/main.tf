resource "random_string" "suffix" {
  length  = 5
  special = false
  upper   = false
  numeric = true
}

locals {
  # RG, Log Analytics, App Insights, ACA environment, Container App, WAF
  # policy - unique only within the subscription/RG, no charset restriction
  # tight enough to need the random suffix.
  name_prefix = "${var.project}-${var.environment}"

  tags = merge(var.tags, {
    project    = var.project
    env        = var.environment
    managed_by = "terraform"
  })
}

resource "azurerm_resource_group" "this" {
  name     = "rg-${local.name_prefix}"
  location = var.location
  tags     = local.tags
}
