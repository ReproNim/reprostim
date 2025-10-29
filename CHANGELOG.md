# 0.7.17 (Wed Oct 29 2025)

#### 📝 Documentation

- Provide basic CLAUDE.md to read context from generic .ai/context.md [#195](https://github.com/ReproNim/reprostim/pull/195) ([@yarikoptic](https://github.com/yarikoptic))

#### Authors: 1

- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.7.16 (Tue Oct 28 2025)

#### 🐛 Bug Fix

- Harmonize/refactor `reprostim` container build and `PsychoPy` [#193](https://github.com/ReproNim/reprostim/pull/193) ([@yarikoptic](https://github.com/yarikoptic) [@vmdocua](https://github.com/vmdocua))
- Extend `video-audit` command with external tools like `qr` and `nosignal` [#192](https://github.com/ReproNim/reprostim/pull/192) ([@vmdocua](https://github.com/vmdocua))
- Add shellcheck testing [#187](https://github.com/ReproNim/reprostim/pull/187) ([@yarikoptic](https://github.com/yarikoptic) [@vmdocua](https://github.com/vmdocua))
- Fix and improve `videos.tsv` video durations statistics [#186](https://github.com/ReproNim/reprostim/pull/186) ([@vmdocua](https://github.com/vmdocua))

#### 🏠 Internal

- Add linkchecker in RTD docs [#191](https://github.com/ReproNim/reprostim/pull/191) ([@vmdocua](https://github.com/vmdocua))
- Replace `cd` with `working-directory` pattern and upgrade GO up to v1.20 [#190](https://github.com/ReproNim/reprostim/pull/190) ([@vmdocua](https://github.com/vmdocua))

#### 🧪 Tests

- Upgrade `PsychoPy` to version 2025.2.0 and fix docker container libs [#185](https://github.com/ReproNim/reprostim/pull/185) ([@vmdocua](https://github.com/vmdocua))

#### Authors: 2

- Vadim Melnik ([@vmdocua](https://github.com/vmdocua))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.7.15 (Mon Sep 15 2025)

#### 🐛 Bug Fix

- Create `video-audit` tool to analyze all recorded videos #1 [#179](https://github.com/ReproNim/reprostim/pull/179) ([@vmdocua](https://github.com/vmdocua))
- Integrate reprostim package with PsychoPy experiment scripts and examples #1 [#174](https://github.com/ReproNim/reprostim/pull/174) ([@vmdocua](https://github.com/vmdocua))
- Fixes for `reprostim-videocapture` config issues [#170](https://github.com/ReproNim/reprostim/pull/170) ([@vmdocua](https://github.com/vmdocua))

#### 🏠 Internal

- Notes from today session to configure reprostim on reproinner [#164](https://github.com/ReproNim/reprostim/pull/164) ([@yarikoptic](https://github.com/yarikoptic) [@vmdocua](https://github.com/vmdocua))

#### Authors: 2

- Vadim Melnik ([@vmdocua](https://github.com/vmdocua))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.7.14 (Wed Jul 30 2025)

#### 🐛 Bug Fix

- Add testing of synchronization script with virtual screen buffer [#167](https://github.com/ReproNim/reprostim/pull/167) ([@vmdocua](https://github.com/vmdocua))
- Streamline container recipes generation: do not bother with version in the recipe name, place in the folder of the script [#156](https://github.com/ReproNim/reprostim/pull/156) ([@yarikoptic](https://github.com/yarikoptic))

#### 🏠 Internal

- Move "Skip Restart Recording" logs to verbose level [#166](https://github.com/ReproNim/reprostim/pull/166) ([@vmdocua](https://github.com/vmdocua))
- Provide custom filter function for Psychopy logs [#165](https://github.com/ReproNim/reprostim/pull/165) ([@vmdocua](https://github.com/vmdocua))
- Setup CI/CD container workflow action [#158](https://github.com/ReproNim/reprostim/pull/158) ([@vmdocua](https://github.com/vmdocua))

#### Authors: 2

- Vadim Melnik ([@vmdocua](https://github.com/vmdocua))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.7.13 (Wed May 14 2025)

#### 🐛 Bug Fix

- Fixes timesync-stimuly issues found during container setup on reproiner for automatic calibration [#155](https://github.com/ReproNim/reprostim/pull/155) ([@vmdocua](https://github.com/vmdocua))

#### Authors: 1

- Vadim Melnik ([@vmdocua](https://github.com/vmdocua))

---

# 0.7.12 (Fri May 09 2025)

#### 🐛 Bug Fix

- Extend `timesync-stimuli` script to support short TRs (500ms and smaller) [#150](https://github.com/ReproNim/reprostim/pull/150) ([@vmdocua](https://github.com/vmdocua))

#### Authors: 1

- Vadim Melnik ([@vmdocua](https://github.com/vmdocua))

---

# 0.7.11 (Fri May 02 2025)

#### 🐛 Bug Fix

- Re-release and point SVG diagram link to RTD site, #125. [#149](https://github.com/ReproNim/reprostim/pull/149) ([@vmdocua](https://github.com/vmdocua))

#### ⚠️ Pushed to `master`

- Re-release and point SVG diagram link to RTD site, #125. ([@vmdocua](https://github.com/vmdocua))

#### Authors: 1

- Vadim Melnik ([@vmdocua](https://github.com/vmdocua))

---

# 0.7.10 (Fri May 02 2025)

#### 🐛 Bug Fix

- User-oriented documentation website (sphinx and RTD) [#145](https://github.com/ReproNim/reprostim/pull/145) ([@vmdocua](https://github.com/vmdocua) [@yarikoptic](https://github.com/yarikoptic))

#### 🏠 Internal

- Generate  `repronim-reprostim-0.7.9` container metadata [#144](https://github.com/ReproNim/reprostim/pull/144) ([@vmdocua](https://github.com/vmdocua))

#### Authors: 2

- Vadim Melnik ([@vmdocua](https://github.com/vmdocua))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.7.9 (Wed Mar 12 2025)

#### 🐛 Bug Fix

- Establish turnkey system for calibration/timing, automate timesync-stimuli [#139](https://github.com/ReproNim/reprostim/pull/139) ([@vmdocua](https://github.com/vmdocua))

#### ⚠️ Pushed to `master`

- Clarify the purpose of scripts under tools/ ([@yarikoptic](https://github.com/yarikoptic))

#### Authors: 2

- Vadim Melnik ([@vmdocua](https://github.com/vmdocua))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.7.8 (Fri Feb 07 2025)

#### 🐛 Bug Fix

- Fixes basic tests execution under conda-forge #2 [#138](https://github.com/ReproNim/reprostim/pull/138) ([@vmdocua](https://github.com/vmdocua))

#### ⚠️ Pushed to `master`

- Make psychopy optional in audiocodes. ([@vmdocua](https://github.com/vmdocua))

#### Authors: 1

- Vadim Melnik ([@vmdocua](https://github.com/vmdocua))

---

# 0.7.7 (Fri Feb 07 2025)

#### 🐛 Bug Fix

- Fixes basic tests execution under conda-forge. [#137](https://github.com/ReproNim/reprostim/pull/137) ([@vmdocua](https://github.com/vmdocua))

#### Authors: 1

- Vadim Melnik ([@vmdocua](https://github.com/vmdocua))

---

# 0.7.6 (Fri Feb 07 2025)

#### 🐛 Bug Fix

- Update container recipe and make sure it builds on typhon using singularity [#136](https://github.com/ReproNim/reprostim/pull/136) ([@vmdocua](https://github.com/vmdocua))

#### 🏠 Internal

- Fixed hatch test errors and configured hatch-test environment [#135](https://github.com/ReproNim/reprostim/pull/135) ([@vmdocua](https://github.com/vmdocua))

#### Authors: 1

- Vadim Melnik ([@vmdocua](https://github.com/vmdocua))

---

# 0.7.5 (Wed Jan 29 2025)

#### 🐛 Bug Fix

- Fixed 'SoundDeviceSound' object has no attribute 'duration' error [#134](https://github.com/ReproNim/reprostim/pull/134) ([@vmdocua](https://github.com/vmdocua))

#### Authors: 1

- Vadim Melnik ([@vmdocua](https://github.com/vmdocua))

---

# 0.7.4 (Tue Jan 28 2025)

#### 🐛 Bug Fix

- Provided additional documentation for reprostim CLI environment setup and hatch-based build [#133](https://github.com/ReproNim/reprostim/pull/133) ([@vmdocua](https://github.com/vmdocua))

#### Authors: 1

- Vadim Melnik ([@vmdocua](https://github.com/vmdocua))

---

# 0.7.3 (Tue Jan 28 2025)

#### 🐛 Bug Fix

- Fixed hatch versioningit configuration [#131](https://github.com/ReproNim/reprostim/pull/131) ([@vmdocua](https://github.com/vmdocua))

#### Authors: 1

- Vadim Melnik ([@vmdocua](https://github.com/vmdocua))

---

# 0.7.2 (Wed Jan 22 2025)

#### 🐛 Bug Fix

- Fix a typo by codespell [#127](https://github.com/ReproNim/reprostim/pull/127) ([@yarikoptic](https://github.com/yarikoptic))

#### ⚠️ Pushed to `master`

- Fixup changelog after a little screwed up auto run ([@yarikoptic](https://github.com/yarikoptic))

#### Authors: 1

- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.7.1 (Wed Jan 22 2025)

#### 🏠 Internal

- Use versioningit with hatch to get version based on git [#126](https://github.com/ReproNim/reprostim/pull/126) ([@yarikoptic](https://github.com/yarikoptic))

#### Authors: 1

- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# 0.7.0 (Wed Jan 22 2024)

First annotated release for auto. There were no automated releases before.
Library went through restructuring and now we are ready with uploads to PyPI.
