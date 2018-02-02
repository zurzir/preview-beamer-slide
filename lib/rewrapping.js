exports.createRewrapper = function(atomEditor) {
    var RewrappingTools = {
        editor: null,

        empty_line_for_latex: function (line) {
            if (line.match(/^\s*$/))
                return true;
            if (line.match(/\\(begin|end|section|subsection|chapter|paragraph)\{[^\}]*\}/))
                return true;
            if (line.match(/(^|[^\\])%/))
                return true;
            if (line.match(/^\s*\\(pause)\s*$/))
                return true;
            if (line.match(/^\s*(\${1,2}|\\\[|\\\])\s*$/))
                return true;
            return false;
        },

        line_begins_with_item: function (line) {
            if (line.match(/^\s*\\(item|exerc|subexe)(\s|\[[^\]]*)/))
                return true;
            return false;
        },

        myrewrap: function () {
            this.domyrewrap(false);
        },

        myrejoin: function () {
            this.domyrewrap(true);
        },

        domyrewrap: function (joinonly) {

            var e = this.editor;

            // initialize line span
            var fromLine = e.get_cur_line();
            var toLine = fromLine;
            var hasSelection = e.has_selection();

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
                if (this.empty_line_for_latex(e.get_line_text(fromLine))) {
                    e.edit_abort();
                    return;
                }

                // no text selection present: search for start & end of paragraph
                while (fromLine > 0 &&
                    !this.line_begins_with_item(e.get_line_text(fromLine)) &&
                    !this.empty_line_for_latex(e.get_line_text(fromLine - 1))) --fromLine;
                var isitem = this.line_begins_with_item(e.get_line_text(fromLine));
                while (toLine < e.get_number_lines() - 1 &&
                    !this.empty_line_for_latex(e.get_line_text(toLine + 1)) &&
                    (!isitem || !this.line_begins_with_item(e.get_line_text(toLine + 1)))) ++toLine;
            }

            // nothing to be done
            if (fromLine == toLine && joinonly) {
                e.edit_abort();
                return;
            }

            // initialize wrap columns
            var wrapColumn = 80;
            var startIndent = "";

            // if there are spaces in front of first line
            var regexp = /^(\s*)\S/;
            var mat = regexp.exec(e.get_line_text(fromLine));
            if (mat != null) {
                startIndent = mat[1];
            }

            wrapColumn -= startIndent.length;

            e.edit_begin();

            // if text ends in the last line, then after removing
            // we need to add a new line in the beginning
            beginLine = "";
            if (toLine == e.get_number_lines() - 1)
                beginLine = "\n";

            // remove lines and trim everything
            var lines = e.remove_many_lines(fromLine, toLine);
            for (var i = 0; i < lines.length; i++)
                lines[i] = lines[i].trim();
            var text = lines.join(" ");

            // if we only want to join the lines
            if (joinonly) {
                e.insert_line(fromLine, beginLine + startIndent + text);
                e.edit_end();
                return;
            }

            // as long as the text is too long, creates a new line
            var newlines = [];
            var countloop = 0; // evita bugs e travar
            while (text.length >= wrapColumn && countloop++ < 150) {
                // find break point

                // try back first
                var wrapAt = wrapColumn;
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
                newlines.push(startIndent + text.substr(0, wrapAt));
                text = text.substr(wrapAt).trim();
            }
            // line for residual text
            if (text.length > 0)
                newlines.push(startIndent + text);

            // inserts lines
            e.insert_line(fromLine, beginLine + newlines.join("\n"));

            e.edit_end();
        },
    };

    RewrappingTools.editor = {
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
        // gets first line in selection
        get_first_line_sel: function() {
            return atomEditor.getSelectedBufferRange().start.row;
        },
        // gets last line in selection
        get_last_line_sel: function() {
            return atomEditor.getSelectedBufferRange().end.row;
        },
        // informs whether there is a nomempty selection
        has_selection: function() {
            return atomEditor.getSelectedText() != '';
        },
        // starts editing
        edit_begin: function () {
            // atomEditor.createCheckpoint();
        },
        // ends editing
        edit_end: function () {
            // atomEditor.groupChangesSinceCheckpoint();
        },
        // ends editing
        edit_abort: function () {
            atomEditor.abortTransaction();
        },
        // remove line and put cursor at the beginning of next line
        remove_line: function (line_num) {
            atomEditor.setCursorBufferPosition([line_num, 0])
            atomEditor.deleteLine();
        },
        // insert line text and put cursor at the beginning of next line
        insert_line: function (line_num, text) {
            atomEditor.setCursorBufferPosition([line_num, 0]);
            atomEditor.insertText(text + "\n");
        },
        // remove multiple lines
        remove_many_lines: function (fromLine, toLine) {
            var n = toLine - fromLine + 1;
            var lines = [];
            for (var i = 0; i < n; i++) {
                lines.push(this.get_line_text(fromLine));
                this.remove_line(fromLine);
            }
            return lines;
        },
        move_to: function (line, col) {
            atomEditor.setCursorBufferPosition([line, col]);
        }
    };

    return RewrappingTools;
}
