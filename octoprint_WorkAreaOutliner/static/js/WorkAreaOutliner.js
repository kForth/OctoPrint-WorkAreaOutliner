/*
 * View model for OctoPrint-WorkAreaOutliner
 *
 * Author: Kestin Goforth
 * Based on work from: Ricardo Riet Correa
 * License: AGPLv3
 */
$(function() {
    function WorkAreaOutlinerViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];
        self.printerState = parameters[1];
        self.temperatureState = parameters[2];
        
        self.initializeSettings = function () {
            self.updateSettingsVisibility = function () {
                // Hide XY Feedrate input if feedrate src is not custom
                $("#workAreaOutliner-customFeedrateXY").toggleClass('hidden',
                    $("#workAreaOutliner-feedrateSrc select > option:selected").val() != "custom"
                );
                // Hide Z Feedrate input if Z is disabled or feedrate src is not custom
                $("#workAreaOutliner-customFeedrateZ").toggleClass('hidden',
                    $("#workAreaOutliner-zAxisEnable input").prop('checked') == false ||
                    $("#workAreaOutliner-feedrateSrc select > option:selected").val() != "custom"
                );
                //Hide Z End Mode input if Z is disabled
                $("#workAreaOutliner-zEndMode").toggleClass('hidden',
                    $("#workAreaOutliner-zAxisEnable input").prop('checked') == false
                );
                //Hide XY Park Position input if XY End Mode is not park
                $("#workAreaOutliner-xyParkPosition").toggleClass('hidden',
                    $("#workAreaOutliner-xyEndMode select > option:selected").val() != "park"
                );
                //Hide XY Park Coords input if XY End Mode is not park or XY Park Location is not custom
                $("#workAreaOutliner-xParkCoord, #workAreaOutliner-yParkCoord").toggleClass('hidden',
                    $("#workAreaOutliner-xyEndMode select > option:selected").val() != "park" ||
                    $("#workAreaOutliner-xyParkPosition select > option:selected").val() != "custom"
                );
                //Hide Z Park Position input if Z is disabled or Z End Mode is not park
                $("#workAreaOutliner-zParkPosition").toggleClass('hidden',
                    $("#workAreaOutliner-zAxisEnable input").prop('checked') == false ||
                    $("#workAreaOutliner-zEndMode select > option:selected").val() != "park"
                );
                //Hide Z Park Coords input if Z is disabled, Z End Mode is not park, or Z Park Location is not custom
                $("#workAreaOutliner-zParkCoord").toggleClass('hidden',
                    $("#workAreaOutliner-zAxisEnable input").prop('checked') == false ||
                    $("#workAreaOutliner-zEndMode select > option:selected").val() != "park" ||
                    $("#workAreaOutliner-zParkPosition select > option:selected").val() != "custom"
                );
            };
            
            // Add event listeners to inputs
            $("#workAreaOutliner-settings input").on('change', self.updateSettingsVisibility);
            $("#workAreaOutliner-settings select").on('change', self.updateSettingsVisibility);

            // Add event
            $("#settings_plugin_WorkAreaOutliner_link").on('click', self.updateSettingsVisibility);
        };

        self.initializeButton = function() {
            // Setup "Outline" button with square icon
			self.outlineBtn = $(`<button>`)
                .addClass("btn")
                .attr("id", "job_outline")
                .attr('title', 'Outline Work Area')
                .text("Outline WA")
                .click(self.onOutlineBtnClick);
            
            // Add "Outline" button to print-control div
            var btnContainer = $('#control-jog-general > div'); //$('#job_print').parent();
            btnContainer.append(self.outlineBtn);

		};

        self.onOutlineBtnClick = function() {            
            $.ajax({
                url: API_BASEURL + "plugin/WorkAreaOutliner",
                type: "POST",
                data: JSON.stringify({
                    command: "outline"
                }),
                contentType: "application/json; charset=UTF-8",
                error: function(resp){
                    // Show Error Notification
                    new PNotify({
                        title: "Work Area Outline Failed",
                        text: resp.responseText,
                        hide: true,
                        buttons: {
                            sticker: false,
                            closer: true
                        },
                        type: "error"
                    });
                },
                success: function(resp){
                    var _fmt = e => e.toFixed(3); //.padStart(7);
                    // Show Success Notification
                    new PNotify({
                        title: "Outlining Work Area",
                        text: [
                                `X = ${_fmt(resp['X'][0])}  to  ${_fmt(resp['X'][1])}`,
                                `Y = ${_fmt(resp['Y'][0])}  to  ${_fmt(resp['Y'][1])}`,
                                `Z = ${_fmt(resp['Z'][0])}  to  ${_fmt(resp['Z'][1])}`
                            ].join('\n'),
                        hide: true,
                        buttons: {
                            sticker: false,
                            closer: true
                        },
                        type: "info"
                    });
                },
            });
        };

        // Check if the button should be enabled.
        self.buttonEnabled = function() {
            // Button should be enabled if all criteria are met
            return !self.temperatureState.isPrinting()      // Not currently printing
                && self.loginState.isUser()                 // User is logged in
                && self.printerState.filename() != null;    // File is selected
        }

        self.updateButton = function() {
			self.outlineBtn.attr('disabled', !self.buttonEnabled());
		};
        
		self.initializeSettings();
		self.initializeButton();
		self.fromCurrentData = function() { self.updateButton(); };
		self.updateButton();
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: WorkAreaOutlinerViewModel,
        dependencies: [ "loginStateViewModel", "printerStateViewModel", "temperatureViewModel"],
        elements: []
    });
});
