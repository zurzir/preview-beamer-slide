#!/usr/bin/env python3

import argparse
import os.path
import re
import subprocess
from glob import glob

TEMP_FILE_BASE = "beamerprevframe"
TEMP_FILE = TEMP_FILE_BASE + ".tex"
TEMP_PDF = TEMP_FILE_BASE + ".pdf"


def read_lines(filename):
    with open(filename) as f:
        content = f.readlines()
    return content


def has_preamble(lines):
    for i, line in enumerate(lines):
        if i >= 20:
            break
        if re.match(r"\s*\\documentclass", line):
            return True
    return False


def extract_preamble(lines):
    s = ""
    for line in lines:
        if re.match(r"\s*\\begin\{document\}", line):
            break
        s += line
    return s


def find_mainfile(texfile, tex_lines):
    "Returns: main_lines, mainfile"
    if has_preamble(tex_lines):
        return texfile, tex_lines
    tex_dir = os.path.dirname(texfile)
    for name in sorted(glob(os.path.join(tex_dir, "*.tex"))):
        if name == texfile or os.path.basename(name) == TEMP_FILE:
            continue
        lines = read_lines(name)
        if has_preamble(lines):
            return name, lines
    raise Exception("No preamble found")


def check_for_custom_args(lines, args):
    for line in lines:
        m = re.match(r"\s*%!preview\[([^\[\]]*)\]", line)
        if m is None:
            continue
        for conf, val in map(lambda x: x.split("=", 2), m.group(1).split(",")):
            conf = conf.strip()
            val = val.strip()
            # FIXME: setting compiler or previewer is potentially insecure
            if conf == "mainfile":
                args.mainfile = val
            elif conf == "nbefore":
                args.nbefore = int(val)
            elif conf == "nafter":
                args.nafter = int(val)
            elif conf == "include_surroundings":
                args.include_surroundings = val.lower() == "true" or val == "1"
            elif conf == "extract_header":
                args.extract_header = val.lower() == "true" or val == "1"
            elif conf == "previewer":
                args.previewer = val
            elif conf == "compiler":
                args.compiler = val
            elif conf == "nopreview":
                args.nopreview = val.lower() == "true" or val == "1"
            elif conf == "handout":
                args.handout = val != "false"
            # assert False, args
        return True
    return False


def check_for_mainfile(lines, args):
    for line in lines:
        m = re.match(r"\s*%\s*!\s*TEX\s*root\s*=(.*)", line)
        if m is None:
            continue
        tex_dir = os.path.dirname(args.texfile)
        args.mainfile = os.path.join(tex_dir, m.group(1).strip())
        return True
    return False


def extract_frame(lines, args):
    """
    Finds a series of frames around a given line number and extracts
    the range immediately befor such frames

    returns: frame, first_line_in_range

    """

    # número de separadores inclui o frame atual
    nafter = args.nafter + 1

    parse_custom_args = True

    # procuara linha de início
    begin_line = 0
    n = 0
    for i in range(args.linenum, -1, -1):
        if re.match(r"\s*(\\begin\{frame\}|\\frame\{)", lines[i]):
            n += 1

            # analisa configurações uma vez
            if parse_custom_args and i > 0 and check_for_custom_args([lines[i - 1]], args):
                parse_custom_args = False

            # atingiu mais separadores do que o esperado, mas não encontrou
            # separador de fim de surrounding
            if n > args.nbefore + 1:
                break
            else:
                begin_line = i
                if n == args.nbefore + 1 and not args.include_surroundings:
                    break

        # já encontrou os separadores esperados, procura até
        # fim do frame anterior, inclusão de arquivo ou
        # marcas %% de surrounding
        elif n == args.nbefore + 1 and re.match(
            r"\s*(\\end\{frame\}|\\if|\\input|\\begin\{document\}|\\section|\\subsection|%%)",
            lines[i],
        ):
            begin_line = i + 1
            break

    if n == 0:
        raise Exception("Nenhum frame encontrado")

    # procuara linha de fim
    end_line = len(lines) - 1
    n = 0
    for i in range(args.linenum, len(lines)):
        if re.match(r"\s*\\end\{frame\}", lines[i]):
            n += 1

            # atingiu mais separadores do que o esperado, mas não encontrou
            # separador de fim de surrounding
            if n > args.nafter + 1:
                break
            else:
                end_line = i
                if n == args.nafter + 1 and not args.include_surroundings:
                    break

        # já encontrou os separadores esperados, procura até
        # início do frame posterior, inclusão de arquivo ou
        # marcas %% de surrounding
        elif n >= args.nafter + 1 and re.match(
            r"\s*(\\begin\{frame\}|\\frame\{|\\if|\\input|\\end\{document\}|\\section|\\subsection|%%)",
            lines[i],
        ):
            end_line = i - 1
            break

    return "".join(lines[begin_line : end_line + 1]), begin_line, end_line


def extract_header(lines, linenum):
    """
    extracts the first few lines in a file before any frame
    and strictly before the given line number

    return: header
    """

    header = ""
    for i in range(linenum):
        if re.match(r"\\begin\{(frame|document)\}|\\(frame|section|subsection)\{", lines[i]):
            break
        header += lines[i]

    return header


def create_prevfile(args):
    tex_lines = read_lines(args.texfile)

    check_for_custom_args(tex_lines[:3], args)
    if not args.mainfile:
        check_for_mainfile(tex_lines[:3], args)
    if args.mainfile:
        main_lines = read_lines(args.mainfile)
    else:
        args.mainfile, main_lines = find_mainfile(args.texfile, tex_lines)

    preamble = extract_preamble(main_lines)
    frames_text, first_frame_line, last_frame_line = extract_frame(tex_lines, args)
    if args.extract_header:
        header = "" if args.mainfile == args.texfile else extract_header(tex_lines, first_frame_line)
    else:
        header = ""
    if args.handout:
        args.before_preample += "\\PassOptionsToClass{handout}{beamer}\n"

    contents = args.before_preample
    contents += preamble
    contents += "\\begin{document}\n"
    contents += header
    if args.hack_synctex:
        cur_line = contents.count("\n")
        if cur_line < first_frame_line:
            contents += "\n" * (first_frame_line - cur_line)
    contents += frames_text
    contents += "\\end{document}\n"

    return contents


def main():
    parser = argparse.ArgumentParser(description="Prevê um frame do beamer.")
    parser.add_argument(
        "-l",
        dest="linenum",
        required=True,
        type=int,
        help="Número da linha do arquivo",
    )
    parser.add_argument(
        "-t",
        dest="texfile",
        required=True,
        help="Nome do arquivo",
    )
    parser.add_argument(
        "-m",
        dest="mainfile",
        default=None,
        help="""
            Nome do arquivo do preâmbulo ou nenhum para usar o mesmo arquivo do
            frame; se não encontrar nas primeiras linhas, então procura por arquivos
            .tex que tenham \\documentclass e estejam no mesmo diretorio
            """,
    )
    parser.add_argument(
        "-a",
        dest="nbefore",
        type=int,
        default=0,
        help="Número da frames antes",
    )
    parser.add_argument(
        "-d",
        dest="nafter",
        type=int,
        default=0,
        help="Número da frames depois",
    )
    parser.add_argument(
        "-s",
        dest="include_surroundings",
        action="store_false",
        help="""
            Desabilita a inclusão dos arredores dos frames
            (normalmente usados para comandos gerais; os arredores
            podem ser delimitados por comentários que começam com %%
            """,
    )
    parser.add_argument(
        "-r",
        dest="extract_header",
        action="store_false",
        help="""
            Desabilita a inclusão das primeiras linhas
            do arquivo
            """,
    )
    parser.add_argument(
        "-p",
        dest="previewer",
        default="evince",
        help="visualizador do pdf (argumentos separados por espaço)",
    )
    parser.add_argument(
        "-c",
        dest="compiler",
        default="pdflatex -synctex=1 -interaction=nonstopmode -shell-escape",
        help="copilador do pdf (argumentos separados por espaço)",
    )
    parser.add_argument(
        "-n",
        dest="nopreview",
        action="store_true",
        help="desabilita visualização de pdf",
    )
    parser.add_argument(
        "-x",
        dest="hack_synctex",
        action="store_true",
        help="Habilita hack do synctex para voltar ao arquivo original",
    )
    parser.add_argument(
        "-b",
        dest="before_preample",
        default="",
        help="Concatena antes do preâmbulo",
    )
    parser.add_argument(
        "-o",
        dest="handout",
        action="store_true",
        help="Adiciona no início preâmbulo `\\PassOptionsToClass{handout}{beamer}`",
    )
    args = parser.parse_args()
    args.linenum -= 1  # linha começa do zero no vetor do python

    # cria arquivo temporário
    contents = create_prevfile(args)
    main_dir = os.path.dirname(args.mainfile)
    tmpfile = os.path.join(main_dir, TEMP_FILE)
    with open(tmpfile, "w") as f:
        f.write(contents)

    previewer_command = args.previewer.split()
    compiler_command = args.compiler.split()

    subprocess.check_call(compiler_command + [TEMP_FILE], timeout=300, cwd=main_dir)

    syncfile = f"{TEMP_FILE_BASE}.synctex"
    if args.hack_synctex:
        subprocess.check_call(["gunzip", f"{syncfile}.gz"], cwd=main_dir)
        sed_exp = f"s#^Input:1:.*#Input:1:{os.path.realpath(args.texfile)}#"
        subprocess.check_call(["sed", "-re", sed_exp, "-i", f"{syncfile}"], cwd=main_dir)
        subprocess.check_call(["gzip", f"{syncfile}"], cwd=main_dir)

    if not args.nopreview:
        subprocess.Popen(previewer_command + [TEMP_PDF], cwd=main_dir)
        assert False, previewer_command

    # se não faz preview, então faz um hack no synctex.gz para direcionar para
    # o arquivo correto


main()
