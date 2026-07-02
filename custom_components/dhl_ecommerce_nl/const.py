"""Constants for the DHL eCommerce (NL) integration."""

DOMAIN = "dhl_ecommerce_nl"

# Poll every 30 minutes. Do NOT lower this: the API is unofficial and a high
# request rate risks rate-limiting or a temporary account block.
DEFAULT_SCAN_INTERVAL = 1800

# Categories that count as "in transit" / not yet delivered. Mirrors the
# original community multiscrape template.
IN_TRANSIT_CATEGORIES = {
    "PROBLEM",
    "CUSTOMS",
    "DATA_RECEIVED",
    "EXCEPTION",
    "INTERVENTION",
    "IN_DELIVERY",
    "LEG",
    "UNDERWAY",
    "UNKNOWN",
}
