output "resource_group_name" {
  value = azurerm_resource_group.this.name
}

output "container_registry_login_server" {
  description = "Push images here from CI: docker push <this>/vastrochart-compute:<tag>"
  value       = azurerm_container_registry.this.login_server
}

output "container_app_fqdn" {
  description = "Direct Container Apps URL - bypasses Front Door/WAF, useful for debugging."
  value       = azurerm_container_app.this.ingress[0].fqdn
}

output "front_door_endpoint_hostname" {
  description = "Public hostname to actually use - WAF + DDoS protected, this is what api.vastrochart.com should CNAME to."
  value       = azurerm_cdn_frontdoor_endpoint.this.host_name
}

output "api_management_gateway_url" {
  value = azurerm_api_management.this.gateway_url
}

output "key_vault_name" {
  value = azurerm_key_vault.this.name
}

output "application_insights_connection_string" {
  sensitive = true
  value     = azurerm_application_insights.this.connection_string
}
