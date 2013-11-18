import QtQuick 2.0
import io.thp.pyotherside 1.0
import UC 1.0

ApplicationWindow {
    id : rWin
    //color : "green"
    //anchors.fill : parent
    width : 640
    height : 480
    Text {
        text : "hello world"
    }

    // properties
    property string guiID : "unknown"
    //property real speedMS : rWin.get("speedTest", 120, function(value){speedMS = value})

    property variant c

    property variant mapPage

    property variant pages : {
        // pre-load the toplevel pages
        "MapPage" : mapPage
        /*
        "Menu" : loadPage("MenuPage"),
        "OptionsMenu" : loadPage("OptionsMenuPage"),
        "InfoMenu" : loadPage("InfoMenuPage"),
        "MapMenu" : loadPage("MapMenuPage"),
        "ModeMenu" : loadPage("ModeMenuPage"),
        */
    }

    Python {
        id : python
        Component.onCompleted: {
            addImportPath('.');
            //importModule('pdb', function() {})
            importModule_sync('sys')
            importModule_sync('pdb')
            importModule_sync('modrana')
            // fake the argv
            //call_sync('setattr','sys' , 'argv' ,'["modrana.py", "-u", "qt5", "-d", "pc"]')
            evaluate('setattr(sys, "argv" ,["modrana.py", "-u", "qt5", "-d", "pc"])')
            console.log('sys.argv faked')
            call_sync('modrana.start')
            evaluate("print('ASDASDASDASDASDASDASD')")
            evaluate("print(modrana.gui)")
            //guiID = evaluate("modrana.gui.getIDString()")
            call("modrana.gui.getIDString", [], function(result){
                guiID = result
            })

            // Python initialization done,
            // initialize the rest of QML
            rWin.__init__()

        }
        onError: {
            // when an exception is raised, this error handler will be called
            console.log('python error: ' + traceback);

        }
    }

    Button {
        anchors.bottom : parent.bottom
        anchors.right : parent.right
        text : "debug"
        onClicked : {
            //console.log(rWin.set("speedTest", 1337))
            //console.log(rWin.get_sync("speedTest", 1234))
            //console.log(rWin.get("speed", 120, function(value){speedMS = value}))
            //console.log(speedMS)
            console.log(rWin.get_sync("speedTest", 1234))
            //console.log(python.evaluate('modrana.gui.get("speedTest")'))
            console.log(python.evaluate('pdb.set_trace()'))

        }
    }

    function __init__() {
        // Do all startup tasks depending on the Python
        // backend being loaded
        console.log("__init__ running")

        // load the constants
        // (including the GUI style constants)
        rWin.c = python.call_sync("modrana.gui.getConstants", [])

        rWin.mapPage = loadPage("MapPage")
        rWin.initialPage = rWin.mapPage
        rWin.pageStack.push(rWin.mapPage)

        console.log(rWin.mapPage)
        console.log(rWin.pageStack)
        console.log(rWin.pageStack.initialItem)
    }

    //property variant mapPage : loadPage("MapPage")

    function loadPage(pageName) {
        console.log("loading page: " + pageName)
        var component = Qt.createComponent(pageName + ".qml");
        if (component.status == Component.Ready) {
            return component.createObject(rWin);
        } else {
            console.log("loading page failed: " + pageName + ".qml")
            console.log("error: " + component.errorString())
            return null
        }
    }

    /* looks like object ids can't be stored in ListElements,
     so we need this function to return corresponding menu pages
     for names given by a string
    */

    function getPage(pageName) {
        console.log("GET PAGE")
        console.log(pageName)

        var newPage
        if (pageName == null) { //signal that we should return to the map page
            newPage = mapPage
        } else { // load a page
            var fullPageName = pageName + "Page"
            newPage = pages[pageName]
            if (!newPage) { // is the page cached ?
                // load the page and cache it
                newPage = loadPage(fullPageName)
                if (newPage) { // loading successful
                    pages[pageName] = newPage // cache the page
                } else { // loading failed, go to mapPage
                    newPage = mapPage
                }
            }
        }
        return newPage

    /* TODO: some pages are not so often visited pages so they could
    be loaded dynamically from their QML files ?
    -> also, a loader pool might be used as a rudimentary page cache,
    but this might not be needed if the speed is found to be adequate */
    }

    function push(pageName) {
        // TODO: instantiate pages that are not in the
        // dictionary
        if (pageName == null) { // null -> back to map
            //TODO: check if the stack can over-fil
            //console.log("BACK TO MAP")
            rWin.pageStack.pop(null,!animate)
        } else {
            console.log("PUSH " + pageName)
            rWin.pageStack.push(getPage(pageName),null,!rWin.animate)
        }
    }


    // Working with options
    function get(key, default_value, callback) {
        //python.call("modrana.gui.get", [key, default_value], callback)
        console.log("running " + callback)

        python.call("modrana.gui.get", [key, default_value])
        return default_value
    }

    function get_auto(key, default_value, target_property) {
        //python.call("modrana.gui.get", [key, default_value], callback)
        console.log("get called")
        console.log(key)
        console.log(default_value)
        console.log(target_property)
        python.call("modrana.gui._get", [key, default_value], function(returned_value) {
            console.log("callback running")
            console.log(target_property)
            console.log(returned_value)
            console.log("done running")
            //target_property=returned_value
            target_property=9001
        })
        return default_value
    }

    function get_sync(key, default_value, callback) {
        return python.call_sync("modrana.gui.get", [key, default_value])
    }

    function set(key, value) {
        python.call("modrana.gui.set", [key, value])
    }

    function set_sync(key, value) {
        python.call_sync("modrana.gui.set", [key, value])
    }
}
