# `secrets`

Serves as an access point to the secrets table in the cloud database so that
secrets don't have to be hardcoded into the apps. Various actions require access
and tokens beyond what most staff is allowed to have, so secrets ensure that
only people who should be able to access a certain resource are able to access
it. Restricted to admins.
