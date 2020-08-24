# 61A Auth

This tool allows applications to access Google Drive and Piazza by wrapping the two APIs in a much simpler OKPy-based interface.

## Quickstart

To start, visit [auth.apps.cs61a.org](https://auth.apps.cs61a.org) and register a client with a unique `client_name`. Keep track of the `secret` returned after you register a client - you can't see it again!

The `secret` lets applications access any Google Document or Sheet that is shared with the service account, as well as private Piazza posts. The service account email address can be seen at  [auth.apps.cs61a.org](https://auth.apps.cs61a.org). **IMPORTANT: If the `secret` is compromised, _IMMEDIATELY_ go to [auth.apps.cs61a.org](https://auth.apps.cs61a.org) and recreate the client with a new `secret`**, as anyone with the `secret` can access sensitive information shared with the service account.

## Basic Usage

### Drive

To read a Google Document, ensure that the service account has access to it, either by making the document visible to "anyone with the link" or by sharing it with the service account directly. Then, you can read the Google Document by making a POST request to `auth.apps.cs61a.org/google/read_document` with the document `url` as a JSON-encoded POST parameter, along with the `client_name` and `secret` For example, in Python, you can do
```python
import requests

text = requests.post("https://auth.apps.cs61a.org/google/read_document", json={
    "url": "https://docs.google.com/document/d/10xo4ofWCnYbmmNBGDGQqVfpOZVo/edit",
    "client_name": "my-client",
    "secret": "my-secret"
}).json()
```
The JSON-encoded body of the response will be the plain text content of that document.

To read a Google Sheet (e.g. to use one to configure an application), make an analogous POST request to `https://auth.apps.cs61a.org/google/read_spreadsheet` with the same parameters before, except also include the parameter `sheet_name` to indicate which sheet of the spreadsheet you want to export. For instance, you can do
```python
import requests

data = requests.post("https://auth.apps.cs61a.org/google/read_spreadsheet", json={
    "url": "https://docs.google.com/spreadsheets/d/1sUeanmzo_Kj1HaXM2v0/edit",
    "sheet_name": "Sheet5",
    "client_name": "my-client",
    "secret": "my-secret",
}).json()
```
The body of the response will be a `List[List[String]]`, with the outer list containing each row until the last non-empty row, and the inner list containing each cell in its corresponding row until the last non-empty cell. As before, it will be JSON-encoded.

To write a Google spreadsheet, make sure the service account can write to it, and then run

```python
import requests

text = requests.post("https://auth.apps.cs61a.org/google/write_spreadsheet", json={
    "url": "https://docs.google.com/document/d/10xo4ofWCnYbmmNBGDGQqVfpOZVo/edit",
    "sheet_name",
    "content": [["A1", "B1", "C1"], ["A2", "B2", "C2"]],
    "client_name": "my-client",
    "secret": "my-secret"
}).json()
```

Where `content` is in the safe format as the return value of `read_spreadsheet`. The response should be `{"success" : True}`

### Piazza
To interact with Piazza, make an authorized POST request to `auth.apps.cs61a.org/piazza/<action>`, where `<action>` is the desired action to take. Pass in the boolean JSON-encoded parameter `staff` to determine whether the action should be taken using a service account acting as a student or as a member of staff. Pass in the boolean parameter `test=true` to use the test Piazza - otherwise, the live Piazza will be used.

These actions correspond to methods of the same name on a `Network` object from the `piazza-api` Python package. To pass arguments into this method call, supply them as additional JSON keys in the POST request. The keys `client_name`, `secret`, and `staff` will be removed from the method call. The JSON-encoded method response will be returned.

For example, to list recent posts on Piazza as seen by a student, you can make the request
```python
import requests

recents = requests.post("https://auth.apps.cs61a.org/piazza/get_feed", json={
    "limit": 150,
    "staff": False,
    "client_name": "my-client",
    "client_secret": "my-secret",
}).json()
```

## Advanced Usage
To programmatically create a client, make a POST request to `/api/request_key` with an OKPy cookie corresponding to an account with staff access to the okpy course `cal/cs61a/CURR_SEMESTER`. You can generate such a cookie by running `python3 ok --get-token` and storing it in the cookie `dev_token`. For the remainder of this section, all POST requests will require such a cookie to be in place.

To revoke a key corresponding to a particular client, make a POST request to `/api/revoke_key?client_name=<CLIENT_NAME>` with the `client_name` parameter set to the name of the desired client whose key is being revoked.

To revoke all keys that have never been used to handle a request, make a POST request to `/api/revoke_all_unused_keys`. You can also visit this link in the browser directly while signed into OKPy to perform the same action.

To revoke *ALL* keys that have been issued, even those currently in use, make a POST request to `/api/DANGEROUS_revoke_all_keys`. In production, it should be very rare that this needs to be done - consider revoking individual keys by visiting the website or invoking the `revoke_key` API on individual clients.

## Deployment Instructions
To quickly deploy an update, run `make deploy`. When deploying for the first time, you must first create a MySQL database linked to the app by running `dokku mysql:create auth auth`, before deploying. After deploying, you must visit [auth.apps.cs61a.org/google/config](https://auth.apps.cs61a.org/google/config) and [auth.apps.cs61a.org/piazza/config](https://auth.apps.cs61a.org/piazza/config) and set everything up before the homepage will start working.

## Obtaining a Google Service Account
Go to [console.cloud.google.com](https://console.cloud.google.com), create a project, then go to `IAM & admin -> Service accounts` and create a new account. You do not need to give this account a role, but you must download a file containing a JSON private key and upload it to the 61A Auth service.

## Development Instructions
 - Clone the repository and install the dependencies in `src/requirements.txt`.
 - Open `src/oauth_client.py` and change the `CONSUMER_KEY` and `SECRET` variables to correspond to a valid okpy OAuth client. Contact the maintainer of this project to obtain these variables.
 - Install and set up `mysql`. In `mysql`, run `CREATE DATABASE account_proxy;`.
 - Then run `src/app.py`, and the server should start.
