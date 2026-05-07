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

### Requirement: Department Authorization For Unrecognized Visitors

The new platform scaffold SHALL support a department authorization flow after a visitor identifies a resident or department without a trusted face match.

#### Scenario: Identified visit triggers department contact

- **GIVEN** the initial greeting already happened
- **AND** there is no trusted face match
- **AND** the visitor identifies a resident or department
- **WHEN** VIGILIA evaluates the turn for `MatIA`
- **THEN** it SHALL return a `contact_department` decision
- **AND** it SHALL preserve the target department in session memory

#### Scenario: Department approves entry

- **GIVEN** a session is waiting for department authorization
- **WHEN** VIGILIA receives an `approved` authorization result for that session
- **THEN** it SHALL return an open decision

#### Scenario: Department denies entry

- **GIVEN** a session is waiting for department authorization
- **WHEN** VIGILIA receives a `denied` authorization result for that session
- **THEN** it SHALL return a denial decision
- **AND** it SHALL not open the gate

#### Scenario: Department does not answer and no registered visit exists

- **GIVEN** a session is waiting for department authorization
- **AND** there is no registered visit fallback for the session
- **WHEN** VIGILIA receives a `no_response` authorization result
- **THEN** it SHALL return a denial decision
- **AND** it SHALL inform that there was no response from the target department

#### Scenario: Department does not answer but a registered visit exists

- **GIVEN** a session is waiting for department authorization
- **AND** there is a registered visit fallback with a 4-digit code
- **WHEN** VIGILIA receives a `no_response` authorization result
- **THEN** it SHALL request the 4-digit authorization code instead of opening immediately

#### Scenario: Registered visit code is valid

- **GIVEN** a session is waiting for a registered visit code
- **WHEN** the visitor provides the expected 4-digit code
- **THEN** VIGILIA SHALL return an open decision

#### Scenario: Registered visit code is invalid

- **GIVEN** a session is waiting for a registered visit code
- **WHEN** the visitor provides a different 4-digit code
- **THEN** VIGILIA SHALL return a denial decision
- **AND** it SHALL not open the gate

### Requirement: Department Authorization Event Runtime

The new platform scaffold SHALL expose a runtime contract for department authorization requests and responses by session.

#### Scenario: Department contact request is emitted

- **GIVEN** VIGILIA returns `contact_department` for a session
- **WHEN** the pipeline persists integration artifacts
- **THEN** it SHALL write a department authorization request for that session

#### Scenario: Department response event is consumed

- **GIVEN** a department authorization response exists for a known session
- **WHEN** the department response watcher runs
- **THEN** it SHALL evaluate the response through the same session memory used by `MatIA`
- **AND** it SHALL persist a processed result artifact
