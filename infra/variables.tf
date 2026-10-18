variable "subscription_id" {
  description = "Azure subscription to deploy into (vac-prod)."
  type        = string
}

variable "project" {
  description = "Short project name, used as a naming prefix. Keep lowercase/alnum - some resources (ACR, Key Vault, Front Door endpoint, API Management) require globally-unique, charset-restricted names and this gets reused in those."
  type        = string
  default     = "vastrochart"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "prod"
}

variable "location" {
  description = "Azure region for all resources."
  type        = string
  default     = "eastus"
}

variable "container_image" {
  description = "Container image for the compute app. Defaults to a public placeholder so the Container App can be created before CI (docs/06-roadmap.md Week 3's GitHub Actions task) has ever pushed a real image to ACR. Switch this to \"<acr_login_server>/vastrochart-compute:<tag>\" once that pipeline exists."
  type        = string
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}

variable "container_target_port" {
  description = "Port the container actually listens on. The bootstrap placeholder image listens on 80 (verified by running it locally) - the real vastrochart-compute image listens on 8080 (its Dockerfile EXPOSEs that port). Switch this to 8080 in the same apply as switching container_image."
  type        = number
  default     = 80
}

variable "apim_publisher_name" {
  description = "Publisher name shown in the API Management developer portal."
  type        = string
  default     = "VAstroChart"
}

variable "apim_publisher_email" {
  description = "Publisher email for API Management (receives service/health notifications from Azure)."
  type        = string
}

variable "tags" {
  description = "Extra tags merged onto every resource, on top of project/environment/managed_by."
  type        = map(string)
  default     = {}
}
