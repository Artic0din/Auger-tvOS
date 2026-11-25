# tvOS Library Playback Documentation

Auger's library-media playback runs on a single AetherEngine route on tvOS.
Apple TV 4K declares the pinned engine/build manifest for online playback and lets AetherEngine probe each source.
The canonical product, ownership, capability, privacy, legal, and validation contract is in [aetherengine-replacement-spec.md](aetherengine-replacement-spec.md), and local ASS subtitle rendering is documented in [ass-subtitles.md](ass-subtitles.md).

## Source entrypoints

- [`AetherPlaybackController.swift`](../../iosApp/iosApp/Screens/Player/AetherPlaybackController.swift) owns library-video loads and transport projection.
- [`AetherLoadSpec.swift`](../../iosApp/iosApp/Screens/Player/AetherLoadSpec.swift) maps Silo Server playback plans into AetherEngine load inputs.
- [`PlaybackTimelineMapper.swift`](../../iosApp/iosApp/Screens/Player/ProtocolV3/PlaybackTimelineMapper.swift) maps the server, stream, and presentation time axes.
- [`PlayerViewModel.swift`](../../iosApp/iosApp/Screens/Player/PlayerViewModel.swift) owns player UI and session behavior while delegating media execution to AetherEngine.
- [`AetherAudioPlaybackController.swift`](../../iosApp/iosApp/Screens/Audio/AetherAudioPlaybackController.swift) owns audiobook media execution through AetherEngine's audio path.

See [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) for pinned AetherEngine, FFmpegBuild, LibDovi, and SwiftLibass provenance and release verification checks.
