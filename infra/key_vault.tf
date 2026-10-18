# <= 24 chars, alnum + hyphens, globally unique.
resource "azurerm_key_vault" "this" {
  name                       = "kv-${var.project}-${random_string.suffix.result}"
  resource_group_name        = azurerm_resource_group.this.name
  location                   = azurerm_resource_group.this.location
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  rbac_authorization_enabled = true
  purge_protection_enabled   = false # keep false while iterating; turn on before real secrets land
  tags                       = local.tags
}

# Lets the deploying user manage secrets directly (Stripe webhook secret,
# API-key hash pepper - docs/08-security.md) once those exist. Not created
# here; that's Week 3's billing/auth task, not this infra pass.
resource "azurerm_role_assignment" "kv_admin_deployer" {
  scope                = azurerm_key_vault.this.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "kv_secrets_user_container_app" {
  scope                = azurerm_key_vault.this.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_container_app.this.identity[0].principal_id
}
