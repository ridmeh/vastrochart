# Name must be alnum-only (no hyphens) and globally unique, hence the
# random suffix rather than local.name_prefix (which has hyphens).
resource "azurerm_container_registry" "this" {
  name                = "acr${var.project}${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  sku                 = "Basic"
  admin_enabled       = false # pulled via the Container App's managed identity - no admin creds
  tags                = local.tags
}
