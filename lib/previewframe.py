#!/usr/bin/env python3

import argparse
import os.path
import re
import subprocess

TEMP_FILE_BASE = 'beamerprevframe'
TEMP_FILE = TEMP_FILE_BASE + '.tex'
TEMP_PDF = TEMP_FILE_BASE + '.pdf'

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


def find_preamble(dirpath, candidate, candidate_lines):
    'Returns: preamble, preamble_file'
    if has_preamble(candidate_lines):
        return extract_pramble(candidate_lines), candidate
    else:
        from glob import glob
        for other in glob(os.path.join(dirpath, '*.tex')):
            if candidate == other:
                continue
            other_lines = read_lines(other)
            if has_preamble(other_lines):
                if os.path.basename(other) == TEMP_FILE:
                    continue
                return extract_pramble(other_lines), other
    raise Exception('No preamble found')


def extract_frame(lines, linenum, nbefore, nafter, include_surroundings):
    '''
    Finds a series of frames around a given line number and extracts
    the range immediately befor such frames

    returns: frame, first_line_in_range

    '''

    # número de separadores inclui o frame atual
    nbefore += 1
    nafter += 1

    # procuara linha de início
    begin_line = 0
    n = 0
    for i in range(linenum, -1, -1):
        if re.match(r'\\begin\{frame\}|\\frame\{', lines[i]):
            n += 1

            # atingiu mais separadores do que o esperado, mas não encontrou
            # separador de fim de sorrounding
            if n > nbefore:
                break
            else:
                begin_line = i
                if n == nbefore and not include_surroundings:
                    break

        # já encontrou os separadores esperados, procura até
        # fim do frame anterior, inclusão de arquivo ou
        # marcas %% de sorrounding
        elif n == nbefore and re.match(r'\\end\{frame\}|\\input|\\begin\{document\}|\\section|\\subsection|%%', lines[i]):
            begin_line = i + 1
            break

    if n == 0:
        raise Exception('Nenhum frame encontrado')

    # procuara linha de fim
    end_line = len(lines) - 1
    n = 0
    for i in range(linenum, len(lines)):
        if re.match(r'\\end\{frame\}', lines[i]):
            n += 1

            # atingiu mais separadores do que o esperado, mas não encontrou
            # separador de fim de sorrounding
            if n > nafter:
                break
            else:
                end_line = i
                if n == nafter and not include_surroundings:
                    break

        # já encontrou os separadores esperados, procura até
        # início do frame posterior, inclusão de arquivo ou
        # marcas %% de sorrounding
        elif n >= nbefore and re.match(r'\\begin\{frame\}|\\frame\{|\\input|\\end\{document\}|\\section|\\subsection|%%', lines[i]):
            end_line = i - 1
            break

    return "".join(lines[begin_line:end_line + 1]), begin_line


def extract_header(lines, linenum):
    '''
    extracts the first few lines in a file before any frame
    and strictly befor the given line number

    return: header
    '''

    h = ''
    for i in range(linenum):
        if re.match(r'\\begin\{(frame|document)\}|\\(frame|section|subsection)\{', lines[i]):
            break
        h += lines[i]

    return h

def create_prevfile(args):

    with open(TEMP_FILE, 'w') as f:
        tex_lines = read_lines(args.texfile)
        dirpath = os.path.dirname(args.texfile)

        # best guess for mainfile canditate
        if args.mainfile:
            candidate = args.mainfile
            candidate_lines = read_lines(candidate)
        else:
            candidate = args.texfile
            candidate_lines = tex_lines

        p, p_file = find_preamble(dirpath, candidate, candidate_lines)

        r, first_frame_line = extract_frame(tex_lines, args.linenum, args.nbefore, args.nafter, args.include_surroundings)
        h = '' if p_file == args.texfile else extract_header(tex_lines, first_frame_line)

        f.write(args.before_preample)
        f.write(p)
        f.write("\\begin{document}\n")
        f.write(h)
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
    parser.add_argument('-s', dest='include_surroundings', action='store_false',
                              help='Desabilita a includsão dos arredores dos frames \
                              (normalmente usados para comandos gerais; os arredores \
                              podem ser delimitados por comentários que começãom com %%')
    parser.add_argument('-p', dest='previewer', default='evince', help='visualizador do pdf (argumentos separados por espaço)')
    parser.add_argument('-c', dest='compiler', default='pdflatex -interaction=nonstopmode -shell-escape', help='copilador do pdf (argumentos separados por espaço)')
    parser.add_argument('-n', dest='nopreview', action='store_true', help='desabilita visualização de pdf')
    parser.add_argument('-b', dest='before_preample', default='',
                              help='Concatena antes do preâmbulo; útil para passar \
                              argumentos para pacotes: e.g.: \\PassOptionsToClass{handout}{beamer}')
    args = parser.parse_args()

    # linha começa do zero no vetor do python
    args.linenum -= 1

    # obtém comandos como listas
    previewer_command = re.split(r' +', args.previewer.strip())
    compiler_command = re.split(r' +', args.compiler.strip())

    create_prevfile(args)
    subprocess.check_call(compiler_command + [TEMP_FILE])
    if not args.nopreview:
        subprocess.Popen(previewer_command + [TEMP_PDF])

main()
