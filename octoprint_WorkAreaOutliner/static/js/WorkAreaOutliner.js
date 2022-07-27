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

        self.settings = parameters[0];
        self.loginState = parameters[1];
        self.printerState = parameters[2];
        self.access = parameters[3];

        self.ignoreMetadata = ko.observable();
        self.zAxisEnable = ko.observable();
        self.homeFirst = ko.observable();
        self.feedrateSrc = ko.observable();
        self.customFeedrateXY = ko.observable();
        self.customFeedrateZ = ko.observable();
        self.xyEndMode = ko.observable();
        self.zEndMode = ko.observable();
        self.xyParkPosition = ko.observable();
        self.zParkPosition = ko.observable();
        self.xParkCoord = ko.observable();
        self.yParkCoord = ko.observable();
        self.zParkCoord = ko.observable();

        self.onBeforeBinding = function () {
            var s = self.settings.settings.plugins.WorkAreaOutliner;
            self.ignoreMetadata(s.ignoreMetadata);
            self.zAxisEnable(s.zAxisEnable);
            self.homeFirst(s.homeFirst);
            self.feedrateSrc(s.feedrateSrc);
            self.customFeedrateXY(s.customFeedrateXY);
            self.customFeedrateZ(s.customFeedrateZ);
            self.xyEndMode(s.xyEndMode);
            self.zEndMode(s.zEndMode);
            self.xyParkPosition(s.xyParkPosition);
            self.zParkPosition(s.zParkPosition);
            self.xParkCoord(s.xParkCoord);
            self.yParkCoord(s.yParkCoord);
            self.zParkCoord(s.zParkCoord);

            self.initializeButton();
            self.updateButton();
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
            return !self.printerState.isPrinting()       // Not currently printing
                && self.printerState.filename() != null  // File is selected
                && self.loginState.isUser()              // User is logged in
                && self.loginState.hasPermission(self.access.permissions.CONTROL);  // User has CONTROL permission
        }

        self.updateButton = function() {
			self.outlineBtn.attr('disabled', !self.buttonEnabled());
		};
        self.fromCurrentData = function() {
            self.updateButton();
        };
        
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: WorkAreaOutlinerViewModel,
        dependencies: [
            "settingsViewModel", 
            "loginStateViewModel",
            "printerStateViewModel",
            "accessViewModel"
        ],
        elements: ["#settings_plugin_WorkAreaOutliner"]
    });
});
