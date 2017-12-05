#!/usr/bin/env python3

import argparse
import os.path
import re
import subprocess

# COMPILER_COMMAND = ['xelatex', '-interaction=nonstopmode']
# COMPILER_COMMAND = ['latexmk', '-xelatex']
COMPILER_COMMAND = ['pdflatex', '-interaction=nonstopmode']
#PREVIWER_COMMAND = ['okular', '--unique']
PREVIWER_COMMAND = ['evince']
TEMP_FILE = 'beamerprevframe.tex'


def read_lines(filename):
    with open(filename) as f:
        content = f.readlines()
    return content


def extract_pramble(lines):
    s = ''
    for l in lines:
        if re.match(r'\s*\\begin\{document\}', l):
            break
        s += l
    return s


def has_preamble(lines):
    i = 0
    for l in lines:
        i += 1
        if i > 20:
            break
        if re.match(r'\s*\\documentclass', l):
            return True
    return False


def find_preamble(file, dirpath, lines):
    if has_preamble(lines):
        return extract_pramble(lines)
    else:
        from glob import glob
        for fn in glob(os.path.join(dirpath, '*.tex')):
            if file == fn:
                continue
            fnlines = read_lines(fn)
            if has_preamble(fnlines):
                if os.path.basename(fn) == TEMP_FILE:
                    continue
                return extract_pramble(fnlines)
    raise Exception('No preamble found')


def extract_frame(lines, linenum, nbefore, nafter):

    begin_line = 0
    n = 0
    found = False
    for i in range(linenum, -1, -1):
        if re.match(r'(\\begin\{frame\}|\\frame\{)', lines[i]):
            if n >= nbefore:
                lines[i] = re.sub(r'^.*(\\begin\{frame\}|\\frame\{)', r'\1', lines[i])
                begin_line = i
                found = True
                break
            n += 1

    if not found:
        raise Exception('Nenhum frame encontrado')

    end_line = len(lines)
    n = 0
    for i in range(linenum + 1, len(lines)):
        if re.match(r'(\\begin\{frame\}|\\frame\{)', lines[i]):
            if n >= nafter:
                lines[i] = re.sub(r'^(.*)(\\begin\{frame\}|\\frame\{).*$', r'\1', lines[i])
                end_line = i
                break
            n += 1

        if nafter == n and re.match(r'\\end\{frame\}', lines[i]):
            lines[i] = re.sub(r'^(.*\\end\{frame\}).*$', r'\1', lines[i])
            end_line = i
            break

    return "".join(lines[begin_line:end_line+1])


def create_prevfile(args):

    with open(TEMP_FILE, 'w') as f:
        lines = read_lines(args.texfile)
        dirpath = os.path.dirname(args.texfile)
        if args.mainfile:
            prefile = args.mainfile
            prelines = read_lines(prefile)
        else:
            prefile = args.texfile
            prelines = lines
        p = find_preamble(prefile, dirpath, prelines)
        r = extract_frame(lines, args.linenum, args.nbefore, args.nafter)
        f.write(p)
        f.write("\\begin{document}\n")
        f.write(r)
        f.write("\\end{document}\n")


def main():
    parser = argparse.ArgumentParser(description='Prevê um frame do beamer.')
    parser.add_argument('-l', dest='linenum', required=True, type=int, help='número da linha do arquivo')
    parser.add_argument('-t', dest='texfile', required=True, help='nome do arquivo')
    parser.add_argument('-m', dest='mainfile', default=None, help='nome do arquivo do preâmbulo ou\
                        nenhum para usar o mesmo arquivo do frame; se não encontrar nas primeiras\
                        linhas, então procura por arquivos .tex que tenham \\documentclass e estejam\
                        no mesmo diretorio')
    parser.add_argument('-a', dest='nbefore', type=int, default=0, help='número da frames antes')
    parser.add_argument('-d', dest='nafter', type=int, default=0, help='número da frames depois')
    parser.add_argument('-p', dest='previewer', help='visualizador do pdf')
    parser.add_argument('-n', dest='nopreview', action='store_true', help='desabilita visualização de pdf')
    args = parser.parse_args()

    # linha começa do zero no vetor do python
    args.linenum -= 1

    create_prevfile(args)
    subprocess.check_call(COMPILER_COMMAND + [TEMP_FILE])
    pdffile = re.sub(r'\.tex$', '.pdf', TEMP_FILE)
    if not args.nopreview:
        if args.previewer:
            cmd = re.split(r' +', args.previewer.strip())
        else:
            cmd = PREVIWER_COMMAND
        subprocess.Popen(cmd + [pdffile])

main()
