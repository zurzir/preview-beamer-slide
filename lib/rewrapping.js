var RewrappingTools = {
    // abstract objects
    editor: null,
    format_helper: null,

    myrewrap: function () {
        return this.domyrewrap(false);
    },

    myrejoin: function () {
        return this.domyrewrap(true);
    },

    wrap_text: function (text, wrapColumn, startIndent, extraIndent, commentStart) {

        // as long as the text is too long, creates a new line
        var newlines = [];
        var countloop = 0; // evita bugs e travar
        var startText = startIndent + commentStart;

        while (text.length >= wrapColumn && countloop++ < 150) {

            // guess where to wrap
            var wrapAt = wrapColumn - startText.length;

            // find point to break line

            // try back first
            while (wrapAt > 0 && !text.charAt(wrapAt).match(/\s/))
                wrapAt--;

            // now try forward
            if (wrapAt == 0) {
                wrapAt = wrapColumn;
                while (wrapAt < text.length && !text.charAt(wrapAt).match(/\s/))
                    wrapAt++;
                // no space
                if (wrapAt == text.length)
                    break;
            }

            // find first space
            while (wrapAt - 1 > 0 && text.charAt(wrapAt - 1).match(/\s/))
                wrapAt--;

            // wraps
            newlines.push(startText + text.substr(0, wrapAt));
            text = text.substr(wrapAt).trim();

            // next indent may be different
            startText = startIndent + commentStart + extraIndent;
        }
        // line for residual text
        if (text.length > 0)
            newlines.push(startText + text);

        return newlines;
    },

    // returns true if changed anything
    domyrewrap: function (joinonly) {

        var e = this.editor;
        var f = this.format_helper;

        // initialize line span
        var fromLine = e.get_cur_line();
        var toLine = fromLine;
        var hasSelection = e.has_selection();
        var isitem = false;
        var isComment = f.comment_line(e.get_line_text(fromLine))
        var rc = f.remove_comment;
        if (!isComment)
            rc = function(x) { return x; }
        // wraps only selected lines
        if (hasSelection) {
            fromLine = e.get_first_line_sel();
            toLine = e.get_last_line_sel();
            if (fromLine > toLine) {
                var aux = toLine;
                toLine = fromLine;
                fromLine = aux;
            }
        } else {
            // abort, if the cursor is in an empty line
            if (f.empty_line(rc(e.get_line_text(fromLine)))) {
                return false;
            }

            // no text selection present: search for start & end of paragraph
            while (fromLine > 0 &&
                !f.line_begins_with_item(rc(e.get_line_text(fromLine))) &&
                !f.empty_line(rc(e.get_line_text(fromLine - 1))) &&
                isComment == f.comment_line(e.get_line_text(fromLine - 1))) --fromLine;
            isitem = f.line_begins_with_item(rc(e.get_line_text(fromLine)));
            while (toLine < e.get_number_lines() - 1 &&
                !f.empty_line(rc(e.get_line_text(toLine + 1))) &&
                (!isitem || !f.line_begins_with_item(rc(e.get_line_text(toLine + 1)))) &&
                isComment == f.comment_line(e.get_line_text(fromLine + 1))) ++toLine;
        }

        // nothing to be done
        if (fromLine == toLine && joinonly) {
            // only moves past paragraph for consistency
            e.move_to(fromLine + 1, 0);
            return false;
        }

        // initialize wrap columns
        var wrapColumn = 80;

        // if there are spaces in front of first line, this is indentation
        var startIndent = "";
        var regexp = /^(\s*)\S/;
        var mat = regexp.exec(e.get_line_text(fromLine));
        if (mat != null) {
            startIndent = mat[1];
        }

        // if text is an item, then find out indentation for following lines
        var extraIndent = "";
        if (isitem)
            extraIndent = f.get_item_extra_indent(e.get_line_text(fromLine));

        // get text
        var lines = [];
        for (var i = fromLine; i <= toLine; i++)
            lines.push(rc(e.get_line_text(i)).trim());
        var text = lines.join(" ");

        // setup comment
        var commentStart = "";
        if (isComment)
            commentStart = f.get_comment_start();

        // wrap lines
        var newlines;
        if (joinonly)
            newlines = [startIndent + commentStart + text];
        else
            newlines = this.wrap_text(text, wrapColumn, startIndent, extraIndent, commentStart);

        // checks if text has changed
        var changed = newlines.length != toLine - fromLine + 1
        if (!changed) {
            for (var i = fromLine, j = 0; i <= toLine; i++, j++) {
                if (e.get_line_text(i) != newlines[j]) {
                    changed = true;
                    break;
                }
            }
        }

        // replace lines
        if (changed) {
            e.replace_lines(fromLine, toLine, newlines);
        }

        // moves past paragraph
        e.move_to(fromLine + newlines.length, 0);

        return changed;
    },
};

// formato para latex
var format_helper_for_latex = {
    empty_line: function (line) {
        if (line.match(/^\s*$/))
            return true;
        if (line.match(/\\(begin|end|section|subsection|chapter|paragraph)\{[^\}]*\}/))
            return true;
        if (line.match(/^\s*\\label\{[^\}]*\}\s*$/))
            return true;
        if (line.match(/(^|[^\\])%/))
            return true;
        if (line.match(/^\s*\\(pause)\s*$/))
            return true;
        if (line.match(/^\s*(\${1,2}|\\\[|\\\])\s*$/))
            return true;
        return false;
    },
    comment_line: function (line) {
        if (line.match(/^\s*%/))
            return true;
        return false;
    },
    remove_comment: function (line) {
        var regexp = /^\s*%\s*(.*)$/;
        var mat = regexp.exec(line);
        if (mat != null) {
            return mat[1];
        }
        return line;
    },
    get_comment_start: function () {
        return "% ";
    },
    line_begins_with_item: function (line) {
        if (line.match(/^\s*\\(item|exerc|subexe)(\s|\[[^\]]*)/))
            return true;
        return false;
    },
    get_item_extra_indent: function (_item_line) {
        // apenas ignora a linha
        return "  ";
    },
};

// formato para markdown
var format_helper_for_markdown = {
    empty_line: function (line) {
        if (line.match(/^\s*$/))
            return true;
        if (line.match(/^#{1,6} /))
            return true;
        if (line.match(/^\-{3}/))
            return true;
        if (line.match(/^```/))
            return true;
        return false;
    },
    comment_line: function (_line) {
        return false;
    },
    remove_comment: function (line) {
        return line;
    },
    get_comment_start: function () {
        return "";
    },
    line_begins_with_item: function (line) {
        if (line.match(/^\s*(\*|[1-9]+\.) /))
            return true;
        return false;
    },
    get_item_extra_indent: function (item_line) {
        var regexp = /^\s*(\*|[1-9]+\.) /;
        var mat = regexp.exec(item_line);
        var indent = "";
        if (mat != null) {
            var indent_size = mat[1].length + 1;
            while (indent_size--)
                indent += " ";
        }
        return indent;
    },
};

exports.createRewrapperForAtom = function(atomEditor) {

    // editor para Atom
    var editor_for_atom = {
        // READ ONLY METHODS
        // number of lines
        get_number_lines: function() {
            return atomEditor.getLastBufferRow()+1;
        },
        // get the text of specific line number passed argument
        get_line_text: function(line) {
            return atomEditor.lineTextForBufferRow(line);
        },
        // gets current line
        get_cur_line: function() {
            return atomEditor.getCursorBufferPosition().row;
        },
        // informs whether there is a nomempty selection
        has_selection: function() {
            return atomEditor.getSelectedText() != '';
        },
        // gets first line in selection
        get_first_line_sel: function() {
            return atomEditor.getSelectedBufferRange().start.row;
        },
        // gets last line in selection
        get_last_line_sel: function() {
            return atomEditor.getSelectedBufferRange().end.row;
        },

        // CHANGE METHODS
        replace_lines: function(fromLine, toLine, newlines) {
            atomEditor.transact(function() {
                var newtext = newlines.join("\n") + "\n";
                atomEditor.setTextInBufferRange([[fromLine,0], [toLine+1, 0]], newtext);
            });
        },

        // NAVIGATION METHODS
        move_to: function (line, col) {
            atomEditor.setCursorBufferPosition([line, col]);
        },
    };

    RewrappingTools.editor = editor_for_atom;

    if (atomEditor.getGrammar().scopeName == "text.tex.latex") {
        RewrappingTools.format_helper = format_helper_for_latex;
    } else {
        RewrappingTools.format_helper = format_helper_for_markdown;
    }

    return RewrappingTools;
}


//  ADICIONA SCRIP
// %SCRIPT
// var exports = {};
// include('/home/tom/Documentos/projects/preview-beamer-slide/lib/rewrapping.js');
// exports.createRewrapperForTexstudio().myrewrap();
exports.createRewrapperForTexstudio = function () {

    // editor para Texstudio
    var editor_for_ts = {
        // READ ONLY METHODS
        // number of lines
        get_number_lines: editor.document().lineCount,
        // get the text of specific line number passed argument
        get_line_text: editor.text,
        // gets current line
        get_cur_line: cursor.lineNumber,
        // informs whether there is a nomempty selection
        has_selection: cursor.hasSelection,
        // gets first line in selection
        get_first_line_sel: cursor.lineNumber,
        // gets last line in selection
        get_last_line_sel: cursor.anchorLineNumber,

        // CHANGE METHODS
        replace_lines: function(fromLine, toLine, newlines) {
            // does nothing
            var newtext = newlines.join("\n") + "\n";
            editor.setCursor(editor.document().cursor(fromLine, 0, toLine+1, 0));
            editor.replaceSelectedText(newtext);
        },

        // NAVIGATION METHODS
        move_to: function (line, col) {
            editor.setCursor(editor.document().cursor(line, col));
        },
    };

    RewrappingTools.editor = editor_for_ts;

    RewrappingTools.format_helper = format_helper_for_latex;

    return RewrappingTools;
}
