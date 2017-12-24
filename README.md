# HTTP-API-Proxy

HTTP-API-Proxy is an easy way to add an API to your application.
It's a transparent proxy that checks either a header or a query parameter
for an API key. It features:

- Dead simple endpoints for adding, removing, and describing api keys.
- Simple setup.
- Highly Configurable.

# Quickstart

The easiest way to use this project is via docker.


```
docker run -p 8080:8080 -e CHECK_QUERY=apiKey -e ADMIN_API_KEY=hunter2 -e FORWARD_HOST=www.google.ca  dpbriggs/http-api-proxy
```

And visit [localhost:8080/?apiKey=hunter2](localhost:8080/?apiKey=hunter2).


## Usage

Set the header `api-key` to a valid API Key. If it properly authenticates, 
the request will passed to the host specified by `FORWARD_HOST`, and the response
will be returned. If the `CHECK_QUERY` variable is set, the query parameter
`$CHECK_QUERY` will be checked and authenticated.

## Example

```
# Create an API Key with a quota of two.
# The admin api key is hunter2.
$ curl localhost:8080/hunter2/add/2
{
  "key": "80c265a97f06446388856590c97fdc86",
  "message": "success",
  "total": "2"
}
# Now lets use this api key
$ curl -H "api-key:80c265a97f06446388856590c97fdc86" localhost:8080
<!DOCTYPE html>
<html lang=en>
  <meta charset=utf-8>
...(truncated)... 
# Let try it again...
$ curl -H "api-key:80c265a97f06446388856590c97fdc86" localhost:8080
<!DOCTYPE html>
<html lang=en>
  <meta charset=utf-8>
...(truncated)... 
# Once more...
$ curl -H "api-key:80c265a97f06446388856590c97fdc86" localhost:8080
{
  "error": "Rate Exceeded. Please contact us to increase your limit",
  "type": "RateExceeded"
}
```

## API Key Actions

All API key actions follow the pattern `/<admin_api_key>/<action>/<*args>`.

### Adding API Keys

To add the API Key `bar` with a usage cap of 10000, use the
`/add/<total>/<`

```
$ curl http://localhost:8080/hunter2/add/10000/bar
{
  "key": "bar", 
  "message": "success", 
  "total": "10000"
}
```

To have the server generate the key just don't include `/bar`,
use the `/add/` action:

```
$ curl http://localhost:8080/hunter2/add/10000
{
  "key": "f0789b0b86b645568be7d93d59d91139", 
  "message": "success", 
  "total": "10000"
}
```

### Removing API Keys

To remove the API Key `bar`, use the `/rm/` action:
```

$ curl http://localhost:8080/hunter2/ls/bar
{
  "message": "success", 
  "removed": "bar"
}

```


### Describing an API Key

To find the remaining API usage for the key `bar`, use
the `/ls/` action.

```
$ curl http://localhost:8080/hunter2/ls/bar
{
  "key": "bar", 
  "message": "success", 
  "ls": 7878
}
```


Thanks!
