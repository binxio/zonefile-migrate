variable domain_name {
  description = "domain name to create zone for"
  type        = string
}

variable resource_record_sets {
  description = "DNS resource record sets in this domain"
  type = list(object({
    name = string
    type = string
    ttl  = number
    rrdatas = list(string)
  }))
}
resource "google_dns_managed_zone" "managed_zone" {
  name     = replace(trimsuffix(var.domain_name, "."), "/\\./", "-")
  dns_name = var.domain_name
}

resource "google_dns_record_set" "record" {
  for_each     = {for r in var.resource_record_sets: format("%s/%s", r.name, r.type) => r}
  name         = each.value.name
  managed_zone = google_dns_managed_zone.managed_zone.name
  type         = each.value.type
  ttl          = each.value.ttl
  rrdatas      = each.value.rrdatas
}
