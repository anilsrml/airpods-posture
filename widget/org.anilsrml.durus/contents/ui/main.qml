import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PlasmaComponents
import org.kde.kirigami as Kirigami

import "logic.js" as Logic

PlasmoidItem {
    id: root

    readonly property string api: "http://127.0.0.1:47800"
    property var status: null
    readonly property var view: Logic.view(status)

    toolTipMainText: "Duruş: " + view.label
    toolTipSubText: view.detail
    Plasmoid.icon: "user-available"

    function request(method, path) {
        const xhr = new XMLHttpRequest();
        xhr.onreadystatechange = () => {
            if (xhr.readyState !== XMLHttpRequest.DONE) return;
            root.status = xhr.status === 200 ? JSON.parse(xhr.responseText) : null;
        };
        xhr.open(method, api + path);
        xhr.send();
    }

    Timer {
        interval: 500
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: root.request("GET", "/state")
    }

    compactRepresentation: MouseArea {
        Layout.minimumWidth: Kirigami.Units.iconSizes.small
        onClicked: root.expanded = !root.expanded

        Rectangle {
            anchors.centerIn: parent
            width: Math.min(parent.width, parent.height) * 0.6
            height: width
            radius: width / 2
            color: root.view.color
            Behavior on color { ColorAnimation { duration: 300 } }
        }
    }

    fullRepresentation: ColumnLayout {
        Layout.preferredWidth: Kirigami.Units.gridUnit * 16
        spacing: Kirigami.Units.largeSpacing

        RowLayout {
            spacing: Kirigami.Units.largeSpacing
            Rectangle {
                width: Kirigami.Units.iconSizes.medium
                height: width
                radius: width / 2
                color: root.view.color
            }
            ColumnLayout {
                spacing: 0
                Kirigami.Heading { text: root.view.label; level: 2 }
                PlasmaComponents.Label { text: root.view.detail; visible: text !== ""; opacity: 0.7 }
            }
        }

        PlasmaComponents.Button {
            Layout.fillWidth: true
            icon.name: "view-refresh"
            text: "Şu an dik duruyorum"
            enabled: root.status !== null && root.status.state !== "disconnected"
            onClicked: root.request("POST", "/recalibrate")
        }

        PlasmaComponents.Button {
            readonly property bool paused: root.status !== null && root.status.state === "paused"
            Layout.fillWidth: true
            icon.name: paused ? "media-playback-start" : "media-playback-pause"
            text: paused ? "Devam et" : "Duraklat"
            enabled: root.status !== null && root.status.state !== "disconnected"
            onClicked: root.request("POST", paused ? "/resume" : "/pause")
        }

        Item { Layout.fillHeight: true }
    }
}
