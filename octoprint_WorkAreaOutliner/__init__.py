# coding=utf-8
from __future__ import absolute_import
import logging

import octoprint.plugin
from octoprint.util.gcodeInterpreter import gcode
from octoprint_WorkAreaOutliner.slicer_metadata import parse_bbox_from_metadata
from octoprint_WorkAreaOutliner.util import *


class WorkAreaOutlinerPlugin(octoprint.plugin.SimpleApiPlugin,
                   octoprint.plugin.TemplatePlugin,
                   octoprint.plugin.SettingsPlugin,
                   octoprint.plugin.AssetPlugin):

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        
        self._zAxisEnable=False
        self._homeFirst=True
        self._feedrateSrc=FeedrateSource.AUTO
        self._customFeedrateXY=3000  # mm/m
        self._customFeedrateZ=300    # mm/m
        self._xyEndMode=EndMode.PARK
        self._zEndMode=EndMode.PARK
        self._xyParkPosition=ParkPosition.MIN_MAX
        self._zParkPosition=ParkPosition.MIN
        self._xParkCoord=5  # mm
        self._yParkCoord=5  # mm
        self._zParkCoord=5  # mm
        self._ignoreMetadata=False

    ##~~ StartupPlugin
    def on_after_startup(self):
        self._logger.info("WorkAreaOutliner Loaded")

    ##~~ SettingsPlugin
    def get_settings_defaults(self):
        return dict(
            zAxisEnable=False,
            homeFirst=True,
            feedrateSrc=FeedrateSource.AUTO,
            customFeedrateXY=3000,  # mm/m
            customFeedrateZ=300,    # mm/m
            xyEndMode=EndMode.PARK,
            zEndMode=EndMode.PARK,
            xyParkPosition=ParkPosition.MIN_MAX,
            zParkPosition=ParkPosition.MIN,
            xParkCoord=5,  # mm
            yParkCoord=5,  # mm
            zParkCoord=5,  # mm
            ignoreMetadata=False
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

    ##~~ AssetPlugin
    def get_assets(self):
        return {
            "js": ["js/WorkAreaOutliner.js"]
        }

    ##~~ TemplatePlugin
    def get_template_configs(self):
        return [
            {
                "type": "settings",
                "name": "WorkAreaOutliner Plugin",
                "template": "WorkAreaOutliner_settings.jinja2",
                "custom_bindings": True,
            }
        ]

    def get_template_vars(self):
        dict(
            zAxisEnable=self._settings.get(["zAxisEnable"]),
            homeFirst=self._settings.get(["homeFirst"]),
            feedrateSrc=self._settings.get(["feedrateSrc"]),
            customFeedrateXY=self._settings.get(["customFeedrateXY"]),
            customFeedrateZ=self._settings.get(["customFeedrateZ"]),
            xyEndMode=self._settings.get(["xyEndMode"]),
            zEndMode=self._settings.get(["zEndMode"]),
            xyParkPosition=self._settings.get(["xyParkPosition"]),
            zParkPosition=self._settings.get(["zParkPosition"]),
            xParkCoord=self._settings.get(["xParkCoord"]),
            yParkCoord=self._settings.get(["yParkCoord"]),
            zParkCoord=self._settings.get(["zParkCoord"]),
            ignoreMetadata=self._settings.get(["ignoreMetadata"])
        )

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
                bbox = parse_bbox_from_metadata(self._logger, filename)
            if not bbox:
                analyser = gcode()
                analyser.load(filepath)
                analysis = analyser.get_result()
                bounds = analysis['printingArea']
                bbox = {
                    X: (bounds["minX"], bounds["maxX"]),
                    Y: (bounds["minY"], bounds["maxY"]),
                    Z: (bounds["minZ"], bounds["maxZ"])
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

    def _get_feedrates(self):
        if self._feedrateSrc == FeedrateSource.AUTO:
            profile = self._printer_profile_manager.get_current()
            min_xy = min(profile['axes']['x']['speed'], profile['axes']['y']['speed'])
            return min_xy, profile['axes']['z']['speed']
        else:
            return self._customFeedrateXY, self._customFeedrateZ
            
    def _get_end_position(self, bounds):
        if self._xyEndMode == EndMode.MODEL:
            x_end_pos, y_end_pos = sum(bounds[0:2])/2, sum(bounds[2:4])/2
        elif self._xyEndMode == EndMode.PARK:
            x_end_pos, y_end_pos = self._xParkCoord, self._yParkCoord
        else: # self._xyEndMode == EndMode.HOME:
            x_end_pos, y_end_pos = 0, 0

        if self._zEndMode == EndMode.MODEL:
            z_end_pos = bounds[5]
        elif self._zEndMode == EndMode.PARK:
            z_end_pos = self._zParkCoord
        else: # self._zEndMode == EndMode.HOME:
            z_end_pos = 0
                    
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
        self._printer.commands(f"G0 X{first_pt[X_]:0.4f} Y{first_pt[Y_]:0.4f} F{xy_feedrate}")

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

        xy_feedrate, z_feedrate = self._get_feedrates()
        end_pos = self._get_end_position(bbox)
        
        outline_pts = [
            (bbox[X][MIN_], bbox[Y][MIN_]),
            (bbox[X][MIN_], bbox[Y][MAX_]),
            (bbox[X][MAX_], bbox[Y][MAX_]),
            (bbox[X][MAX_], bbox[Y][MIN_]),
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
                "displayName": __plugin_name__,
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
