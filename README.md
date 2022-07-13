
# OctoPrint-WorkAreaOutliner

## Description
This plugin adds an "Outline" button to preview the working area of a Gcode file.

If there is no bounding box in the gcode metadata, WorkAreaOutliner will manually calculate it.

## Slicer Metadata
If using a supported slicer program, this plugin can read the work area from the file metadata.

If metadata is not available, the work area will be automatically calculated.

### Supported Slicers:
- Cura
- PrusaSlicer
- SuperSlicer
- Slic3r
- Lightburn (inherited from OctoPrint-Framer, untested)
- Fusion360 (inherited from OctoPrint-Framer, untested)

## Screenshots:
![Control Tab with Outline button](https://raw.githubusercontent.com/kForth/plugins.octoprint.org/dev/WorkAreaOutliner/assets/img/plugins/WorkAreaOutliner/screen.png)
![Settings screen](https://raw.githubusercontent.com/kForth/plugins.octoprint.org/dev/WorkAreaOutliner/assets/img/plugins/WorkAreaOutliner/settings.png)

## Setup
### Requirements
- Python >= 3.8

### Installation
Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html) or manually using this URL:

    https://github.com/kforth/OctoPrint-WorkAreaOutliner/archive/main.zip

## Usage
### Configuration
After installation restart OctoPrint, go to the Settings tab to configure the plugin.

### Outline Function
- Connect to the machine
- Home the machine (or set origin manually)
- Load the Gcode file
- Navigate to the 'Control' tab and click the 'Outline' button
- Watch the machine as it outlines the bounding box of the work area
  - Be ready to stop the machine to avoid colisions!

### Warnings
- Make sure the machine is homed correctly.
- Make sure the area is clear to avoid colisions.

## License

Copyright © 2022 [Kestin Goforth](https://github.com/kforth/).

Based on work from [Ricardo Riet Correa](https://github.com/rriet/OctoPrint-Framer).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the [GNU Affero General Public License](https://www.gnu.org/licenses/agpl-3.0.en.html) for more details.