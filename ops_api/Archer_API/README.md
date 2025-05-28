# Archer API

For more information on the Archer platform, please visit [this help page](https://help.archerirm.cloud/platform_611/en-us/content/platform/integration/int_api_basics.htm).

The Archer platform has 3 main APIs that can be queried using system provided
credentials.

1) [Web Services API](https://help.archerirm.cloud/platform_611/en-us/content/api/webapi/webhelplanding.htm)
2) [RESTful](https://help.archerirm.cloud/platform_611/en-us/content/api/restapi/webhelplanding.htm)
3) [Content API](https://help.archerirm.cloud/platform_611/en-us/content/api/contentapi/contentapi_overview.htm)

The Web Services API is currently used to pull reports created by a user in the
Archer graphical environment. Please see the [SearchOptions guidlines](https://help.archerirm.cloud/platform_611/en-us/content/api/webapi/xml_formatting_guidelines_for_5.x_search_input.htm)
if you would like to call ArcherServerClient.exec_search with custom options.

The RESTful API is currently used to pull history log data. The RESTful API
requires a contents id to make queries. These ids will be colletively
reffered to as an ArcherServerClient instance's context.

This module provides 2 main classes:

- ArcherAuth
- ArcherClient

## Important Note on Session Maintainence

The ArcherAuth class starts and maintains the session created with the user's
credentials. Session authentication is handled through session tokens. Token are
only valid as long as they are generated from the most recent signing. A new
signing event will invalidate any previously generated token. If you have a need
to access the API and/or UI simultaneously, separate credentials must be used or
you risk invalidating your previous session.

## Important Note on API Availability

The ArcherClient classes are responsible for making the various API
calls and returning data to the user. An instance will have access to data
provisioned to the user. These provisions are made by the Archer system admin
and linked to the credentials used for signing. Please make sure your account
has the necessary provisions before calling ArcherAuth.login().