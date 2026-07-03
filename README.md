# DHL eCommerce (NL) for Home Assistant

Track your incoming **DHL** parcels (the ones you *receive*, via
[my.dhlecommerce.nl](https://my.dhlecommerce.nl/)) in Home Assistant.

This is a native custom integration with a UI config flow — no YAML, no
`command_line`, no shell scripts. You log in once with your DHL account and get
a `sensor.dhl_ecommerce_packages` entity showing how many parcels are on their way, with
full per-parcel details in its attributes.

> ⚠️ **Unofficial API.** This integration uses the same private endpoints as the
> DHL consumer website. DHL can change them at any time, which may break this
> integration without warning. Use at your own risk.

## Why this exists

DHL changed their authentication: the parcels endpoint is now CSRF-protected and
returns **HTTP 401** unless the `XSRF-TOKEN` cookie is echoed back in an
`X-XSRF-TOKEN` request header. The old community `multiscrape` setup couldn't do
that, so it stopped working. This integration performs the correct flow:

1. `POST /api/user/login` → receive session cookies (incl. `XSRF-TOKEN`)
2. `GET /receiver-parcel-api/parcels` with the cookies **plus**
   `X-XSRF-TOKEN: <XSRF-TOKEN value>`

## Installation

### Via HACS (recommended)

1. In HACS, open the three-dot menu → **Custom repositories**.
2. Add this repository URL, category **Integration**.
3. Search for **DHL eCommerce (NL)** and download it.
4. Restart Home Assistant.
5. Go to **Settings → Devices & Services → Add Integration** and search for
   **DHL eCommerce (NL)**. Enter your DHL e-mail and password.

### Manual

Copy the `custom_components/dhl_ecommerce_nl` folder into your Home Assistant
`config/custom_components/` directory and restart Home Assistant, then add the
integration from the UI.

## The sensor

`sensor.dhl_ecommerce_packages` (**DHL eCommerce Packages**)

- **State**: number of parcels currently in transit (categories `PROBLEM`,
  `CUSTOMS`, `DATA_RECEIVED`, `EXCEPTION`, `INTERVENTION`, `IN_DELIVERY`, `LEG`,
  `UNDERWAY`, `UNKNOWN`).
- **Attributes**:
  - `parcels` — list of in-transit parcels (full objects)
  - `delivered` — list of already-delivered parcels
  - `total` — total number of parcels returned

Polls every 30 minutes.

## Example Lovelace card

Will be deliverd soon
```yaml
type: conditional
conditions:
  - condition: numeric_state
    entity: sensor.dhl_ecommerce_packages
    above: 0
card:
  type: markdown
  content: |
    <table>
      <thead><tr><td>Sender</td><td>Date</td><td>Time</td></tr></thead>
      <tbody>
      {% for p in state_attr('sensor.dhl_ecommerce_packages', 'parcels') %}
        {% if p.receivingTimeIndication and 'start' in p.receivingTimeIndication %}
        {% set pc = (p.receiver.address.postalCode if p.receiver and p.receiver.address else '') | replace(' ', '') %}
        {% set tt = 'https://my.dhlecommerce.nl/home/tracktrace/' ~ p.barcode ~ '/' ~ pc %}
      <tr>
        <td><a href="{{ tt }}" target="_blank">{{ p.sender.name }}</a></td>
        <td>{{ as_timestamp(p.receivingTimeIndication.start) | timestamp_custom('%-d %b') }}</td>
        <td>{{ as_timestamp(p.receivingTimeIndication.start) | timestamp_custom('%H:%M') }}</td>
      </tr>
        {% endif %}
      {% endfor %}
      </tbody>
    </table>

```
Is already deliverd (overview for the past 7 days)
```yaml
type: markdown
content: >
  {% set cutoff = now().timestamp() -7*24*3600 %} {% set delivered =
  (state_attr('sensor.dhl_ecommerce_packages', 'delivered') or [])
       | selectattr('receivingTimeIndication', 'defined')
       | sort(attribute='receivingTimeIndication.moment', reverse=True) %}
  <table>
    <thead><tr><td>Sender</td><td>Date</td><td>Time</td></tr></thead>
    <tbody>
    {% for p in delivered %}
      {% set m = p.receivingTimeIndication.moment %}
      {% if m and as_timestamp(m, 0) >= cutoff %}
      {% set pc = (p.receiver.address.postalCode if p.receiver and p.receiver.address else '') | replace(' ', '') %}
      {% set tt = 'https://my.dhlecommerce.nl/home/tracktrace/' ~ p.barcode ~ '/' ~ pc %}
    <tr>
      <td><a href="{{ tt }}" target="_blank">{{ p.sender.name }}</a></td>
      <td>{{ as_timestamp(m) | timestamp_custom('%-d %b') }}</td>
      <td>{{ as_timestamp(m) | timestamp_custom('%H:%M') }}</td>
    </tr>
      {% endif %}
    {% endfor %}
    </tbody>
  </table>

```

## Disclaimer

Not affiliated with or endorsed by DHL. "DHL" is a trademark of Deutsche Post
AG. This project talks to an undocumented, private API and may break at any
time.

