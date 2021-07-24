const _ = require('lodash')

/* global WIKI */

// ------------------------------------
// OpenID Connect Account
// ------------------------------------

const OAuth2Strategy = require('passport-oauth2').Strategy

module.exports = {
  init (passport, conf) {
    passport.use('okpy',
      new OAuth2Strategy({
        authorizationURL: "https://okpy.org/oauth/authorize",
        tokenURL: "https://okpy.org/oauth/token",
        clientID: conf.clientId,
        clientSecret: conf.clientSecret,
        scope: "all",
        callbackURL: conf.callbackURL,
        passReqToCallback: true,
        skipUserProfile: true
    }, async (req, access, refresh, profile, cb) => {
      console.log(access, refresh, profile, cb)
      try {
        const data = await (await fetch(`https://okpy.org/api/v3/user/?access_token=${access}`)).json()
        console.log(data)
        const user = await WIKI.models.users.processProfile({
            providerKey: req.params.strategy,
            profile: {
              name: data.data.name,
              email: data.data.email
            }
          })
          cb(null, user)
        } catch (err) {
          cb(err, null)
        }
      })
    )
  },
  logout (conf) {
    if (!conf.logoutURL) {
      return '/'
    } else {
      return conf.logoutURL
    }
  }
}
