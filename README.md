# Odoo Plugin: Car Fleet-Management Tesla-API integration

**WARNING**: The [Telsa Fleet-API](https://developer.tesla.com/docs/fleet-api) is **NOT FREE TO USE**! Make sure to read [the Telsa API-billing info](https://developer.tesla.com/docs/fleet-api/getting-started/billing-and-limits)!

## Features:

* Query [vehicle data](https://developer.tesla.com/docs/fleet-api/endpoints/vehicle-endpoints#vehicle) from Telsa-API per car configured in odoo-fleet-management
  * A tab-section inside the Odoo-fleet car-view that contains the information queried from the Telsa-API
  * Updating odometer-value
* Plugin settings-section inside the Odoo-fleet-management settings-page
* API-call protocol-page to give you full transparency what the module does (`oxl.fleet.tesla.protocol`)
* A protocol for the Tesla-alerts queried (`oxl.fleet.tesla.alerts`)

----

## Getting Started

* Create a [Telsa Business-Account](https://accounts.tesla.com/business/get-started)

* Create an API-application => [Telsa documentation](https://www.tesla.com/developer-docs) & [Dashboard](https://developer.tesla.com/dashboard)

  Choose 'Only Machine-to-Machine' communication

  Copy the Client-ID and -Secret

  You can limit the API-access [scopes](https://developer.tesla.com/docs/fleet-api/authentication/overview#scopes).

  This plugin calls [these endpoints](https://developer.tesla.com/docs/fleet-api/endpoints/vehicle-endpoints#vehicle) - only read permissions are required (*some can be opted-in or -out in the plugin-settings*):

  * `auth`
  * `vehicles`
  * `vehicles/<vin>/vehicle_data`
  * `vehicles/<vin>/drivers`
  * `vehicles/<vin>/recent_alerts`
  * `vehicles/<vin>/service_data`
  * `dx/vehicles/options?vin=<vin>`

* If your server is behind a proxy or firewall - ensure connections to the Telsa-API are possible:

  * `auth.tesla.com`
  * Server of your Region:
    * EU: `fleet-api.prd.eu.vn.cloud.tesla.com`
    * America: `fleet-api.prd.na.vn.cloud.tesla.com`
    * China: `fleet-api.prd.cn.vn.cloud.tesla.cn`

* Ensure a VIN (`vin_sn`) is configured for your Telsa cars inside Odoo-fleet-management

### Install Plugin

* Make sure to configure a plugins-directory inside your Odoo-server config-file (default: `/etc/odoo/odoo.conf`)

* Add the content of this repository inside a subdirectory of that plugins-path - example: `/var/lib/odoo/plugins/oxl_tesla_api`

* Restart the Odoo-server: `systemtl restart odoo.service`

* Login to Odoo-WebUI with an administrator account

* Go to the plugins-page inside odoo and search for `tesla`

  Choose & click on `Upgrade`

  If any error occurs at the upgrade - there might be an incompatibility with your odoo version or another plugin. You have to troubleshoot it. Maybe also open [an issue](https://github.com/O-X-L/odoo-plugin-car-fleet-tesla-api/issues) so a fix can be added to this repo.

* Go to the Odoo-fleet-management settings

  You should now see a section for the Telsa-plugin.

  Add your API-client & -secret.

  Go through the other settings and choose the options you need.

* Go to the Odoo-groups and add users to the `Tesla Fleet Officer` and `Tesla Fleet Administrator` groups

----

## Known Issues

* Translations (`i18n/*.po`) not working
* Scheduled API-update not working (*odoo cron-jobs seem to have very little documentation and troubleshooting options*)
* Telsa API-key shown in plaintext inside the plugin-settings-page (*sadly, have not found a way to hide it like a password*)
