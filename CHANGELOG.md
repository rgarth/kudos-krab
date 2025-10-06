# Changelog

All notable changes to Kudos Krab will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.2] - 2025-10-02

### Added
- Configurable logging levels via `LOG_LEVEL` environment variable
- Support for ERROR, WARNING, INFO, and DEBUG logging levels
- Better log formatting with timestamps and module names
- Missing `/kk version` and `/kk status` commands to help message

### Changed
- Health check logs moved to DEBUG level to reduce uptime robot noise
- Default logging level remains INFO for backward compatibility

### Fixed
- Users can now discover version and status commands via `/kk help`

## [0.8.1] - 2025-10-02

### Added
- Comprehensive bot status command (`/kk status`)
- Quick version check command (`/kk version`)
- Channel configuration inheritance system
- Support for channel-specific personalities
- Monthly quota configuration per channel
- Timezone configuration per channel
- Leaderboard channel override system

### Changed
- Improved error handling and logging
- Enhanced database connection pooling
- Better personality system with channel-specific overrides

### Fixed
- Database connection issues with Aiven free tier
- Channel configuration persistence
- Leaderboard display formatting

## [0.8.0] - 2025-09-XX

### Added
- Initial release of Kudos Krab
- Slash command support (`/kk`)
- Multi-recipient kudos support
- Monthly leaderboards
- Personal statistics
- Channel-specific configurations
- PostgreSQL database support
- Docker deployment support
- AWS Lambda deployment support
