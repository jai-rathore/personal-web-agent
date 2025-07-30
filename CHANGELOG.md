# Changelog

## [1.1.0] - 2025-07-29

### Added
- **Visitor Feedback System**: Allowing visitors to leave messages
  - New `/api/feedback` endpoint for feedback submission
  - Feedback modal component with friendly, simplified UI
  - SMTP email service for feedback notifications
  - Footer integration with "💬 Share Thoughts" link

### Changed
- **Gemini Model Upgrade**: Switched from `gemini-2.5-pro` to `gemini-2.5-flash`
  - Updated both chat and intent classification models