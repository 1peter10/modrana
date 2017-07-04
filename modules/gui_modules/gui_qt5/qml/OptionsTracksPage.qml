//OptionsTracklogsPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: tracksPage
    headerText : "Tracks"

    content : ContentColumn {
       Label {
            text : qsTr("Tracklog opacity")
        }
        Slider {
            id : tracklogOpacitySlider
            width : parent.width
            stepSize : 0.1
            maximumValue : 1.0
            minimumValue : 0.0
            value : rWin.mapPage.tracklogOpacity
            valueText : ""
            onPressedChanged : {
                // set the value once users
                // stops interacting with the slider
                if (pressed == false) {
                    rWin.mapPage.tracklogOpacity = value
                    rWin.set("qt5GUITracklogOpacity", value)
                }
            }
        }


    }
}