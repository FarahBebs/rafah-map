"""Switch the Rafah.3dm layer groups to match the web Map view menu.

How to run in Rhino 7 or Rhino 8
1. Open rhino/Rafah.3dm
2. Type EditPythonScript and press Enter
    (or Tools → Python → Edit…)
3. Open this file: rhino/Set Map View.py
4. Click Run
5. Choose a view from the list

You can also drag this file onto the Rhino window, or add it as a button.
"""

from __future__ import annotations

import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc

# Parent layer groups created by export_rhino.py
VIEWS = {
    "OpenStreetMap": {
        "on": ["Shared", "01 OpenStreetMap"],
        "off": [
            "02 Basemap AUB",
            "03 Damage AUB",
            "04 3D Map AUB",
            "05 People and Place",
            "06 Heritage",
        ],
        "named_view": "City",
        "note": "Everyday OSM buildings and roads — same as the web default.",
    },
    "Basemap (AUB)": {
        "on": ["Shared", "01 OpenStreetMap", "02 Basemap AUB"],
        "off": [
            "03 Damage AUB",
            "04 3D Map AUB",
            "05 People and Place",
            "06 Heritage",
        ],
        "named_view": "Governorate",
        "note": "Farmland, greenhouses, camps, institutions over OSM buildings.",
    },
    "Damage (AUB)": {
        "on": ["Shared", "03 Damage AUB", "04 3D Map AUB"],
        "off": [
            "01 OpenStreetMap",
            "02 Basemap AUB",
            "05 People and Place",
            "06 Heritage",
        ],
        "named_view": "Governorate",
        "note": "Damage overlays plus extruded AUB damage-coloured buildings.",
    },
    "3D Map (AUB)": {
        "on": ["Shared", "04 3D Map AUB"],
        "off": [
            "01 OpenStreetMap",
            "02 Basemap AUB",
            "03 Damage AUB",
            "05 People and Place",
            "06 Heritage",
        ],
        "named_view": "City",
        "note": "Only the extruded damage buildings — closest to the web 3D Map tab.",
    },
    "People & Place (AUB)": {
        "on": ["Shared", "05 People and Place"],
        "off": [
            "01 OpenStreetMap",
            "02 Basemap AUB",
            "03 Damage AUB",
            "04 3D Map AUB",
            "06 Heritage",
        ],
        "named_view": "People and Heritage",
        "note": "Story pins across Gaza (blue / green / gold by theme).",
    },
    "Heritage (AUB)": {
        "on": ["Shared", "06 Heritage"],
        "off": [
            "01 OpenStreetMap",
            "02 Basemap AUB",
            "03 Damage AUB",
            "04 3D Map AUB",
            "05 People and Place",
        ],
        "named_view": "People and Heritage",
        "note": "Heritage sites and buildings across Gaza.",
    },
}


def find_layer_index(layer_name):
    try:
        index = sc.doc.Layers.FindByFullPath(layer_name, -1)
        if index >= 0:
            return index
    except Exception:
        pass
    for i in range(sc.doc.Layers.Count):
        if sc.doc.Layers[i].Name == layer_name:
            return i
    return -1


def set_layer_tree_visible(layer_name, visible):
    index = find_layer_index(layer_name)
    if index < 0:
        return False
    layer = sc.doc.Layers[index]
    layer.IsVisible = visible
    parent_id = layer.Id
    for i in range(sc.doc.Layers.Count):
        child = sc.doc.Layers[i]
        if child.ParentLayerId == parent_id:
            child.IsVisible = visible
    return True


def restore_named_view(name):
    if not name:
        return
    for i in range(sc.doc.NamedViews.Count):
        info = sc.doc.NamedViews[i]
        if info.Name == name:
            view = sc.doc.Views.ActiveView
            if view:
                view.ActiveViewport.PushViewInfo(info, True)
                view.Redraw()
            return


def main():
    choice = rs.ListBox(
        list(VIEWS.keys()),
        "Same options as the web Map view menu",
        "Rafah map view",
    )
    if not choice:
        return
    config = VIEWS[choice]
    for name in config["off"]:
        set_layer_tree_visible(name, False)
    for name in config["on"]:
        set_layer_tree_visible(name, True)
    restore_named_view(config.get("named_view"))
    sc.doc.Views.Redraw()
    rs.MessageBox(
        "{}\n\nTip: Named views are also under Viewport title → Named Views.".format(config["note"]),
        0,
        choice,
    )


if __name__ == "__main__":
    main()
