## ADDED Requirements

### Requirement: New Platform Repository

The project SHALL provide a separate repository scaffold for the `Mac mini M4 + GDS3725` platform.

#### Scenario: New platform scaffold exists

- **WHEN** the team starts the new hardware integration stage
- **THEN** a dedicated `vigilia-m4-gds3725` repository scaffold SHALL exist
- **AND** it SHALL be separate from the Dahua/Asterisk prototype structure

### Requirement: Asterisk Is Not Required By Default

The new platform architecture SHALL not require Asterisk as a mandatory core runtime dependency.

#### Scenario: Initial architecture is reviewed

- **WHEN** the platform architecture is documented
- **THEN** it SHALL describe audio, decision, TTS and gate services without requiring Asterisk as the default control layer

### Requirement: Safe Test Modes

The new platform scaffold SHALL support safe testing modes.

#### Scenario: Team validates decision logic

- **WHEN** a developer runs the scaffold before hardware integration is complete
- **THEN** the scaffold SHALL provide `decision-only` and `dry-run` modes
- **AND** those modes SHALL avoid real gate actuation

### Requirement: Trusted Face Match Shortcut

The new platform scaffold SHALL support an immediate-open decision path for trusted resident face matches delivered by the device.

#### Scenario: Trusted resident face match is received after the greeting

- **GIVEN** the system already played the initial greeting
- **AND** the device provides a trusted face match for a known resident
- **WHEN** VIGILIA evaluates the turn for `MatIA`
- **THEN** it SHALL return an immediate open decision
- **AND** it SHALL not require an additional conversational clarification step
