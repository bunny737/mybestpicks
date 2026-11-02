# Vendored Bootstrap

Bootstrap **5.3.8** (MIT, see LICENSE), copied unmodified from
`https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/` on 2026-11-02, except that the
trailing `sourceMappingURL` comment was removed from both files (the `.map` files are
not shipped and `ManifestStaticFilesStorage` fails on a missing map).

Served from our own domain through WhiteNoise: no third-party requests from
readers' browsers.

| File | sha256 |
|---|---|
| bootstrap.min.css | 8f8173cb2d8f867274aeb0cb15328e60f490c7f272351e51a55f1dabb486e4ff |
| bootstrap.bundle.min.js | c6f670216aedd2c61ec83102f7e40c1c44114eecd7f37b2edc332757390c386a |

To upgrade by hand (Dependabot is off): download the same two files for the new
version, strip the `sourceMappingURL` comment, update this table and the version in
docs/modules/02-base-layout.md.
