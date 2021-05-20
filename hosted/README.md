# Hosted Apps DNA

This is 61A's stateful app hosting service, a wrapper around
[@itsvs](https://github.com/itsvs)'s [dna](https://dna.vanshaj.dev/) tool.

This app has no local setup, as it is not meant to be run locally. Most of the
code here is just RPC wrappers, which haven't been documented yet, so feel free
to peruse through the code and reference the `dna` docs if you want to
understand this app better.

The `buildserver` deploy script for this app is available
[here](https://github.com/Cal-CS-61A-Staff/cs61a-apps/blob/62ff040c72f63b0258508e72c76d162cf9dcc16a/buildserver/deploy.py#L382).