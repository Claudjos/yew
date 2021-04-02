# Yew Proxy Server

## Overview
Extendable non-blocking IO proxy server.

## Features
- Multiple proxy running on the same instance
- HTTP Proxy
- SOCKS5 Proxy (just CONNECT method)
- Parent Proxy
- Reverse HTTP Proxy
- Rewrite HTTP request URI
- IP subnets allow/block rules
- Host allow/block rules
- Authentication
- Extendable with custom modules for adding features

## Settings
Checkout the [examples](examples/configuration).

## Custom modules
Checkout the [examples](examples/customization).

## Usage
```
python3 -m yew {your_settings_file.yaml}
```

## TODOs
Tests
- Automatically stop the thread used to run the proxy while testing.

Nice functionalities to have
- Import setting from more files
- TLS for servers
- TLS for upstreams
- upstream to server static file
- DNS proxy with rewrite rules