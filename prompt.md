You are working in `/Users/raphael/Coding/badarak`.

Objective: build a tool that can play the organ music for the Armenian Divine Liturgy / Badarak on Sundays when no organist is available.

Requirements:

1. Source material
   - Find a modern, high-quality PDF of the Armenian Divine Liturgy / Badarak that includes the organ score or organ accompaniment pieces.
   - Prioritize official/public church sources only:
     - Armenian Diocese / Eastern Diocese website
     - Armenian Western Diocese website
     - St. Nersess Armenian Seminary
   - Use either Eastern or Western Armenian tradition if that is what the best available official score provides.
   - Save source URLs and citation notes in a local documentation file.
   - Do not redistribute copyrighted material unless the source explicitly permits it; store local PDFs only for personal/local processing.

2. Python environment
   - Create and use a virtual environment named exactly `badarak_venv`.
   - Install dependencies using the most efficient reliable tooling available in the environment.
   - Keep install commands documented so the setup can be repeated.

3. PDF score to MIDI transcription
   - Research and install the best open-source music-score PDF-to-MIDI transcription tool available for this use case.
   - Prefer mature OMR tooling such as Audiveris if it is still the strongest open-source option.
   - Convert the organ score pages from PDF/image score input into MusicXML and/or MIDI.
   - Preserve timing, note durations, ties, rests, key signatures, and meter as accurately as possible.
   - Build a validation workflow:
     - render or inspect the generated MIDI,
     - compare against the score visually/listening-wise,
     - log pages/measures that need manual correction.
   - If fully automatic OMR is not accurate enough, produce a documented correction workflow using MusicXML/MIDI editing tools.

4. Badarak organ MIDI preparation
   - Normalize the result into one organ-focused MIDI track.
   - Keep the file structure organized, for example:
     - `sources/` for source notes and local PDF references,
     - `omr/` for OMR outputs,
     - `midi/` for cleaned MIDI files,
     - `badarak_player/` for playback code,
     - `docs/` for setup and validation notes.
   - Store metadata for each piece/section: title, source page range, tempo, meter, mode/key if known, and validation status.

5. Roland Fantom playback
   - Build a Python playback tool that transmits MIDI notes over USB to a Roland Fantom synthesizer.
   - Use a technique similar to `music_script_python/orchestrator.py`, but simplify it for this project:
     - no multi-track song generation,
     - no stem recording,
     - no production/mastering pipeline,
     - only one organ MIDI track is required.
   - Use `mido` / `python-rtmidi` or the best local MIDI backend for USB MIDI output.
   - Detect available MIDI output ports and select the Roland Fantom port.
   - Send the correct MIDI bank/program changes for a Roland organ patch before playback.
   - Make the organ patch configurable, with a sensible Roland organ default.
   - Include transport controls:
     - play a selected MIDI file,
     - stop safely,
     - optional start-at-measure or start-at-time if practical,
     - list available Fantom/MIDI ports.

6. Safety and reliability
   - Before modifying existing files, create timestamped backups and log:
     - edited filename,
     - backup filename,
     - concise change summary.
   - Do not change the existing full-song music generation behavior in `music_script_python/`.
   - Treat `music_script_python/orchestrator.py` as a reference for Fantom-oriented orchestration, not as the main implementation target.
   - The new Badarak organ player should be separate, minimal, and purpose-built.

7. Verification
   - Verify the virtual environment works.
   - Verify the selected OMR/transcription tool can run locally.
   - Verify at least one score page or short excerpt can be converted to MIDI.
   - Verify the MIDI playback script can list MIDI ports.
   - If the Fantom is connected, verify it can receive the organ patch/program change and play a short test phrase.
   - Document all commands, failures, fixes, and remaining manual correction needs.

Deliverables:
- `README.md` or `docs/setup.md` with setup and usage instructions.
- Source citation notes for the Badarak PDF.
- A repeatable OMR/transcription workflow.
- Cleaned MIDI output for at least one organ section as a proof of concept.
- A single-track Roland Fantom organ playback script.
- A concise verification report showing what was tested.
