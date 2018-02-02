/* jshint esversion: 6 */

const { CompositeDisposable } = require('atom');
const { execFile } = require('child_process');
const path = require('path');

const { createRewrapper } = require('./rewrapping.js');

module.exports = {
    subscriptions: null,
    pyscript: null,

    activate() {
        this.subscriptions = new CompositeDisposable();
        this.subscriptions.add(atom.commands.add('atom-workspace', {
            'preview-beamer-slide:preview': () => this.preview()
        }));
        this.subscriptions.add(atom.commands.add('atom-workspace', {
            'preview-beamer-slide:previous-frame': () => this.navFrame(-1)
        }));
        this.subscriptions.add(atom.commands.add('atom-workspace', {
            'preview-beamer-slide:next-frame': () => this.navFrame(1)
        }));
        this.subscriptions.add(atom.commands.add('atom-workspace', {
            'preview-beamer-slide:rewrap-paragraph': () => this.rewrapParagraph()
        }));
        this.subscriptions.add(atom.commands.add('atom-workspace', {
            'preview-beamer-slide:rejoin-paragraph': () => this.rejoinParagraph()
        }));
        const packpath = atom.packages.getLoadedPackage('preview-beamer-slide').path;
        this.pyscript = path.join(packpath, 'lib', 'previewframe.py');

    },

    deactivate() {
        this.subscriptions.dispose();
    },

    preview() {
        const editor = atom.workspace.getActiveTextEditor();
        if (!editor || !editor.getBuffer()) {
            return;
        }
        if (!editor.getBuffer().file) {
            atom.notifications.addError("Salve o arquivo antes de tentar visualizar.");
            return;
        }

        // FIXME: criar possibilidade de fazer preview sem salvar antes!!
        if (editor.isModified()) {
            editor.save();
        }

        const filepath = editor.getBuffer().file.path;
        const dirpath = path.dirname(filepath);
        const line = editor.getCursorBufferPosition().row + 1;
        const prev = atom.config.get('preview-beamer-slide.previewerPath');
        const args = [this.pyscript, '-t', filepath, '-l', line, '-p', prev];
        const enabled = atom.config.get('preview-beamer-slide.previewerEnable');
        if (!enabled) {
            args.push('-n');
        }

        // console.log(args);
        execFile('python3', args, {
            cwd: dirpath
        }, (error, stdout, stderr) => {
            if (error) {
                atom.notifications.addError("Aconteceu algum erro na compilação do frame.Veja o console.");
                console.log(error);
                console.log(`stdout: ${stdout}`);
                console.log(`stderr: ${stderr}`);
            } else if (!enabled) {
                atom.notifications.addInfo("Arquivo beamerprevframe.pdf gerado.");
            }
        });
    },

    isBeginFrame(line) {
        return;
    },

    navFrame(step = 1) {
        const editor = atom.workspace.getActiveTextEditor();
        if (!editor || !editor.getBuffer())
            return;
        const startrow = editor.getCursorScreenPosition().row;
        const lastrow = editor.getLastScreenRow();
        var foundBeginFrame = false;
        var row = startrow;
        while (row >= 0 && row <= lastrow) {
            if (editor.lineTextForScreenRow(row).match(/\\begin\{frame\}|\\frame\{/) &&
                row + 1 != startrow) {
                foundBeginFrame = true;
                break;
            }
            row += step;
        }
        if (foundBeginFrame) {
            editor.setCursorScreenPosition([row + 1, 0]);
        }
    },

    rewrapParagraph() {
        const editor = atom.workspace.getActiveTextEditor();
        rewrapper = createRewrapper(editor);
        editor.transact(function() {
            rewrapper.myrewrap();
        });
    },

    rejoinParagraph() {
        const editor = atom.workspace.getActiveTextEditor();
        rewrapper = createRewrapper(editor);
        editor.transact(function() {
            rewrapper.myrejoin();
        });
    }

};
