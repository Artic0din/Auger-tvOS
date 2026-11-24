# Auger privacy policy

Auger is a third-party Apple TV client for self-hosted Silo media servers.

## What Auger connects to

Auger connects only to the Silo server addresses you configure and to any local Silo companion devices on your network when you use pairing or remote control.
Auger does not run a cloud backend, user-account service, analytics service, or crash-reporting collector of its own.

## Data stored on your Apple TV

Auger stores the following data locally on your Apple TV using Apple Keychain and App Group storage:

- Saved Silo server addresses and display names
- Session tokens and profile tokens issued by your Silo server
- App preferences, playback preferences, and cached artwork

Removing a server or signing out deletes the associated tokens from Keychain.
Deleting Auger from your Apple TV removes its local preferences and caches.

## Diagnostics

Auger does not send diagnostics or crash reports to any third-party hosted service.
If your Silo server has diagnostics enabled and you choose to send a report from **Settings > Diagnostics**, Auger uploads that report directly to your own Silo server.
You can inspect pending reports before sending or turn crash reporting off in **Settings > Diagnostics**.

## Third-party services

Media metadata, artwork, and subtitles shown in Auger come from your Silo server.
Any external metadata provider configuration is controlled by your server administrator on that server.

## Contact

Questions or privacy reports can be filed at [Artic0din/silo-apple/issues](https://github.com/Artic0din/silo-apple/issues).
