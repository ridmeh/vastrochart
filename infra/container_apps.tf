resource "azurerm_container_app_environment" "this" {
  name                       = "cae-${local.name_prefix}"
  resource_group_name        = azurerm_resource_group.this.name
  location                   = azurerm_resource_group.this.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id
  tags                       = local.tags
}

resource "azurerm_container_app" "this" {
  name                         = "ca-${local.name_prefix}-compute"
  resource_group_name          = azurerm_resource_group.this.name
  container_app_environment_id = azurerm_container_app_environment.this.id
  revision_mode                = "Single"
  tags                         = local.tags

  identity {
    type = "SystemAssigned"
  }

  # Safe to wire in now that azurerm_role_assignment.acr_pull already
  # exists from the bootstrap apply (see git history for why this was
  # commented out on the very first apply - chicken-and-egg with a
  # not-yet-existing identity/role).
  registry {
    server   = azurerm_container_registry.this.login_server
    identity = "System"
  }

  template {
    min_replicas = 1 # always-warm per docs/03-architecture.md - no cold-start on user requests
    max_replicas = 20

    container {
      name   = "vastrochart-compute"
      image  = var.container_image
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = azurerm_application_insights.this.connection_string
      }

      liveness_probe {
        transport = "HTTP"
        port      = 8080
        path      = "/healthz"
      }

      readiness_probe {
        transport = "HTTP"
        port      = 8080
        path      = "/readyz"
      }
    }

    http_scale_rule {
      name                = "http-concurrency"
      concurrent_requests = 50
    }
  }

  ingress {
    external_enabled = true
    target_port      = var.container_target_port
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  # deploy.yml now owns which image is running (az containerapp update on
  # every push to main, ADR-038/039) - without this, the next `terraform
  # apply` would silently roll production back to whatever var.container_image
  # was last set to here, undoing every deploy CI has done since. var.container_image
  # still matters for the very first apply against a brand-new environment,
  # where nothing has deployed yet.
  lifecycle {
    ignore_changes = [template[0].container[0].image]
  }
}

resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.this.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_container_app.this.identity[0].principal_id
}
