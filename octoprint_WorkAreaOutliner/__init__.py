# coding=utf-8
from __future__ import absolute_import
import json
import re

import octoprint.plugin
from octoprint.util.gcodeInterpreter import gcode

import logging

# GCode Command arguments
X = 'X'
Y = 'Y'
Z = 'Z'

# Shorthand for list indeces
_X = 0
_Y = 1
_Z = 2
_MIN = 0
_MAX = 1

class NullBoundException(Exception):
    pass

class WorkAreaOutlinerPlugin(octoprint.plugin.SimpleApiPlugin,
                   octoprint.plugin.TemplatePlugin,
                   octoprint.plugin.SettingsPlugin,
                   octoprint.plugin.AssetPlugin):

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        
        self._zAxisEnable=False
        self._homeFirst=True
        self._feedrateSrc="auto"
        self._customFeedrateXY=3000
        self._customFeedrateZ=300
        self._xyEndMode="restore"
        self._zEndMode="restore"
        self._xyParkPosition="min_min"
        self._zParkPosition="nearbed"
        self._xParkCoord=10
        self._yParkCoord=10
        self._zParkCoord=10
        self._ignoreMetadata=False
        self._ignoreTravelMoves=True
        self._waitForFirstLayer=True
        self._stopAfterFirstLayer=True

    ##~~ StartupPlugin
    def on_after_startup(self):
        self._logger.info("WorkAreaOutliner Loaded")

    ##~~ SettingsPlugin
    def get_settings_defaults(self):
        return dict(
            zAxisEnable=False,
            homeFirst=True,
            feedrateSrc="auto",
            customFeedrateXY=3000,
            customFeedrateZ=300,
            xyEndMode="restore",
            zEndMode="restore",
            xyParkPosition="min_min",
            zParkPosition="nearbed",
            xParkCoord=10,
            yParkCoord=10,
            zParkCoord=10,
            ignoreMetadata=False,
            ignoreTravelMoves=True,
            waitForFirstLayer=True,
            stopAfterFirstLayer=True,
        )

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.initialize()

    def initialize(self):
        self._zAxisEnable=self._settings.get(["zAxisEnable"])
        self._homeFirst=self._settings.get(["homeFirst"])
        self._feedrateSrc=self._settings.get(["feedrateSrc"])
        self._customFeedrateXY=self._settings.get(["customFeedrateXY"])
        self._customFeedrateZ=self._settings.get(["customFeedrateZ"])
        self._xyEndMode=self._settings.get(["xyEndMode"])
        self._zEndMode=self._settings.get(["zEndMode"])
        self._xyParkPosition=self._settings.get(["xyParkPosition"])
        self._zParkPosition=self._settings.get(["zParkPosition"])
        self._xParkCoord=self._settings.get(["xParkCoord"])
        self._yParkCoord=self._settings.get(["yParkCoord"])
        self._zParkCoord=self._settings.get(["zParkCoord"])
        self._ignoreMetadata=self._settings.get(["ignoreMetadata"])
        self._ignoreTravelMoves=self._settings.get(["ignoreTravelMoves"])
        self._waitForFirstLayer=self._settings.get(["waitForFirstLayer"])
        self._stopAfterFirstLayer=self._settings.get(["stopAfterFirstLayer"])

    ##~~ AssetPlugin
    def get_assets(self):
        return {
            "js": ["js/WorkAreaOutliner.js"]
        }

    ##~~ TemplatePlugin
    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    ##~~ SimpleApiPlugin
    def get_api_commands(self):
        return dict(outline=[])

    def on_api_command(self, command, data):
        if command == "outline":
            filename = self._printer.get_current_job()["file"]["path"]
            filepath = self._file_manager.path_on_disk("local", filename)
            bbox = False
            if not bbox:
                bbox = self._get_bbox_from_octoprint_metadata(filename)
            if not self._ignoreMetadata:
                bbox = self._get_bbox_from_slicer_metadata(filepath)
            if not bbox:
                analyser = gcode()
                analyser.load(filepath)
                analysis = analyser.get_result()
                bbox = {
                    X: (analysis["minX"], analysis["maxX"]),
                    Y: (analysis["minY"], analysis["maxY"]),
                    Z: (analysis["minZ"], analysis["maxZ"])
                }
            
            if bbox:   
                self._logger.debug(
                    "Found Work Area: X%0.4f to X%0.4f | Y%0.4f to Y%0.4f | Z%0.4f to Z%0.4f",
                    *bbox[X], *bbox[Y], *bbox[Z]
                )
                self.follow_outline(bbox)
                return bbox, 200
            else:
                self._logger.error("Error, Could not find work area")
                return "Could not find work area.", 500
        else:    
            return "Unknown Command", 500

    def _get_bbox_from_octoprint_metadata(self, filename):
        # Try to get the work area from OctoPrint's analysis
        file_data = self._file_manager.get_metadata("local", filename)
        work_area = (file_data or {}).get('analysis', {}).get('printingArea', False)
        if work_area:
            if work_area['maxX'] != 0:
                self._logger.info("Using Printing Area from OctoPrint Analysis")
                return {
                    X: (work_area["minX"], work_area["maxX"]),
                    Y: (work_area["minY"], work_area["maxY"]),
                    Z: (work_area["minZ"], work_area["maxZ"])
                }
            else:
                self._logger.debug("OctoPrint metadata invalid (maxX == 0)")
        else:
            self._logger.debug("Could not find OctoPrint metadata. File too new?")

        return False
            
    def _get_bbox_from_slicer_metadata(self, filepath):
        # Try to get the work area from metadata left by slicer program
        with open(filepath) as src_file:
            header = src_file.read(1024)  # Read first 1024 bytes for metadata

            # Search for Lightburn file metadata
            if (match := re.search(r'; Bounds:\s*([^\n]*)\s*', header)):
                self._logger.info("Using Work Area from Lightburn Metadata")
                # Looking for the following string pattern:
                # ; Bounds: X18.85 Y204.94 to X185.15 Y387.06
                
                coords = re.match(r'X(-?\d+.?\d*)\s*Y(-?\d+.?\d*)\s*to\s*X(-?\d+.?\d*)\s*Y(-?\d+.?\d*)', match.groups(1))

                return {
                    X: (float(coords.groups(1)), float(coords.groups(3))),
                    Y: (float(coords.groups(2)), float(coords.groups(4))),
                    Z: (0, 0)
                }
            
            # Search for Fusion360 metadata
            elif (match := re.search(r';\s*Ranges table:\s*;\s*(X:.*)\s*;\s*(Y:.*)', header)):
                self._logger.info("Using Work Area from Fusion360 Metadata")
                # Looking for the following string pattern:
                #; Ranges table:
                #; X: Min=-0.5 Max=63.4 Size=63.9
                #; Y: Min=-0.5 Max=25.4 Size=25.9
                
                x_coords = re.match(r'; (X: Min=(-?\d+.?\d*) Max=(-?\d+.?\d*) Size=(-?\d+.?\d*))', match.groups(1))
                y_coords = re.match(r'; (Y: Min=(-?\d+.?\d*) Max=(-?\d+.?\d*) Size=(-?\d+.?\d*))', match.groups(2))

                return {
                    X: (float(x_coords.groups(2)), float(x_coords.groups(3))),
                    Y: (float(y_coords.groups(2)), float(y_coords.groups(3))),
                    Z: (0, 0)
                }
            
            # Search for Slic3r (and derivatives) metadata
            elif (match := re.search(r'; generated by (Slic3r|(Super|Prusa)Slicer)\b', header)):
                self._logger.info(f"Using Work Area from {match.groups(1)} Metadata")
                # Looking for the following string pattern:
                # ; plater:{"center":[237.500000,149.999579,0.000000],"boundingbox_center":[237.500000,149.999579,4.500000],"boundingbox_size":[53.000000,56.424981,9.000000]}

                plater_line = re.search(r'; plater:\s*([^\n]*)\s*', header)
                plater = json.loads(plater_line.groups(1))

                center = plater["center"]
                bbox_center = plater["boundingbox_center"]
                bbox_size = plater["boundingbox_size"]

                return {
                    X: (bbox_center[_X] - bbox_size[_X] / 2, bbox_center[_X] + bbox_size[_X] / 2),
                    Y: (bbox_center[_Y] - bbox_size[_Y] / 2, bbox_center[_Y] + bbox_size[_Y] / 2),
                    Z: (center[_Z], center[_Z] + bbox_size[_Z])
                }
            
            # TODO: Search for Cura metadata

            # TODO: Search for Other Slicer metadata

            else:
                self._logger.warning("Could not find slicer metadata. Unsupported program?")

        return False

    def _get_feedrates(self):
        if self._feedrateSrc == 'auto':
            profile = self._printer_profile_manager.get_current()
            min_xy = min(profile['axes']['x']['speed'], profile['axes']['y']['speed'])
            return min_xy, profile['axes']['z']['speed']
        else:
            return self._customFeedrateXY, self._customFeedrateZ
            
    def _get_end_position(self, initPos, bounds):
        if self._xyEndMode == 'center':
            x_end_pos, y_end_pos = sum(bounds[0:2])/2, sum(bounds[2:4])/2
        elif self._xyEndMode == 'home':
            x_end_pos, y_end_pos = 0, 0
        elif self._xyEndMode == 'park':
            x_end_pos, y_end_pos = self._xParkCoord, self._yParkCoord
        else:  # self._xyEndMode == 'restore':
            x_end_pos, y_end_pos = initPos[:2]

        if self._zEndMode == 'max':
            z_end_pos = bounds[5]
        elif self._zEndMode == 'home':
            z_end_pos = 0
        elif self._zEndMode == 'park':
            z_end_pos = self._zParkCoord
        else:  # self._zEndMode == 'restore':
            z_end_pos = initPos[2]
                    
        return {
            X: x_end_pos,
            Y: y_end_pos,
            Z: z_end_pos
        }

    def _start_outlining(self, z_feedrate):
        # Home Axes
        if self._homeFirst:
            self._printer.commands(f"G28 {'XYZ' if self._zAxisEnable else 'XY'}")
        
        # Absolute Positioning Mode
        self._printer.commands("G90")

        # Raise Z-Axis to travel height
        if self._zAxisEnable:
            self._printer.commands(f"G0 Z10 F{z_feedrate}")

    def _do_outline(self, outline_pts, xy_feedrate, z_feedrate):
        # Move to first outline point
        first_pt = outline_pts.pop(0)
        self._printer.commands(f"G0 X{first_pt[_X]:0.4f} Y{first_pt[_Y]:0.4f} F{xy_feedrate}")

        # Move Z-Axis close to bed
        if self._zAxisEnable:
            self._printer.commands(f"G0 Z5 F{z_feedrate}")

        # Move to each outline point and then back to the first one
        outline_pts.append(first_pt)
        for xPt, yPt in outline_pts:
            self._printer.commands(f"G0 X{xPt:0.4f} Y{yPt:0.4f} F{xy_feedrate}")

    def _end_outline(self, end_pos, xy_feedrate, z_feedrate):
        # Raise Z-Axis from bed
        if self._zAxisEnable:
            self._printer.commands(f"G0 Z10 F{z_feedrate}")
        
        # Move Axes to 'After Outlining' position
        self._printer.commands(f"G0 X{end_pos[X]:0.4f} Y{end_pos[Y]:0.4f} F{xy_feedrate}")
        if self._zAxisEnable:
            self._printer.commands(f"G0 Z{end_pos[Z]:0.4f} F{z_feedrate}")

    def follow_outline(self, bbox):
        self._logger.info("Outlining Work Area")

        init_pos = (0, 0, 0) # TODO: Get current position
        xy_feedrate, z_feedrate = self._get_feedrates()
        end_pos = self._get_end_position(init_pos, bbox)
        
        outline_pts = [
            (bbox[X][_MIN], bbox[Y][_MIN]),
            (bbox[X][_MIN], bbox[Y][_MAX]),
            (bbox[X][_MAX], bbox[Y][_MAX]),
            (bbox[X][_MAX], bbox[Y][_MIN]),
        ]

        self._start_outlining(z_feedrate)
        self._do_outline(outline_pts, xy_feedrate, z_feedrate)
        self._end_outline(end_pos, xy_feedrate, z_feedrate)


    ##~~ Software Update Hook
    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "WorkAreaOutliner": {
                "displayName": "WorkAreaOutliner Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "kforth",
                "repo": "OctoPrint-WorkAreaOutliner",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/kforth/OctoPrint-WorkAreaOutliner/archive/{target_version}.zip",
            }
        }


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "WorkAreaOutliner Plugin"


# Set the Python version your plugin is compatible with below. Recommended is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3.8,<4"  # Only Python 3.8 or newer

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = WorkAreaOutlinerPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
