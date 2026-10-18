# <= 50 chars, alnum + hyphens, globally unique (forms the *.azure-api.net
# hostname). Importing the OpenAPI spec / configuring key tiers & rate
# limits is a separate roadmap task (docs/06-roadmap.md Week 3) - this just
# provisions the empty service.
resource "azurerm_api_management" "this" {
  name                = "apim-${var.project}-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  publisher_name      = var.apim_publisher_name
  publisher_email     = var.apim_publisher_email
  sku_name            = "Consumption_0"
  tags                = local.tags
}
