// Share to JARVIS (round 6): what Safari hands the share extension with a shared page
// (NSExtensionJavaScriptPreprocessingFile in Config/JARVISShare-Info.plist). It only reads: the page's
// title, its address, the words selected on it, and its visible text, cut at 60,000 characters (the
// extension cuts again to fit a question). Nothing on the page is changed or sent anywhere from here.
var PageText = function() {};

PageText.prototype = {
    run: function(parameters) {
        var text = "";
        var selection = "";
        try { text = (document.body && document.body.innerText) ? document.body.innerText : ""; } catch (e) {}
        try { selection = window.getSelection ? String(window.getSelection()) : ""; } catch (e) {}
        parameters.completionFunction({
            "title": document.title || "",
            "url": document.URL || "",
            "selection": selection.substring(0, 20000),
            "text": text.substring(0, 60000)
        });
    },
    finalize: function(parameters) {}
};

var ExtensionPreprocessingJS = new PageText;
