# preview-beamer-slide package

Faz um preview de um slide do beamer e outros utilitários para latex.

## Uso

1. Configure o comando para o previsualizador nas configurações do pacote
2. Coloque o cursor em qualquer linha do frame
3. Aperte alt+l (ou modifique o atalho)

## Navegando pelos frames

1. alt+k vai para frame anterior
2. alt+j vai para próximo frame

## Formatando parágrafos

1. alt+q formata o parágrafo de forma esperta, quebrando na coluna 80 e
   preservando indentação (funciona com item e também no contexto de markdown)
2. alt+z junta todo o parágram em uma única linha

## Comandos locais

O script irá tentar usar uma heurística para incluir comandos locais
definidos no início do arquivo ou imediatemente antes e após o frame. Por exemplo, em

```tex
....
\end{frame}

\newcommand{\mycommand}{Its me}

\begin{frame}
\mycommand
\end{frame}
```

será incluída a definição de `\mycommand`, já que do contrário não seria possível
compilar o frame. Raramente isso pode ser inconveniente (e.g., se o comando
estiver fora de contexto. Nesse casos, utilize `%%` (pelo menos dois símbolos de
percentagem) para delimitar fronteiras, como em:


```tex
\begin{small}

\begin{frame}
  frame anterior
\end{frame}

\end{small}

%%

\newcommand{\mycommand}{Its me}

\begin{frame}
\mycommand
\end{frame}
```

Somente o comando `\mycommand` será incluído. Se removêssemos o `%%`, o `\end{small}`
seria incluído, provocando um erro.

## Frames de contexto

Por padrão, compila só um frame. Se for útil, pode-se configurar para compilar
frames antes ou depois para o contexto.

### Observações

* Compila somente uma vez por eficiência (mesmo que haja referências não
  resolvidas). Execute duas vezes no mesmo frame se for o caso.
* Usa pfdlatex; se precisar mudar, configure para usar xelatex
* Se houver vários arquivos  \*.tex  com \\documentclass, então copia o
  preâmbulo de qualquer um. Não há problema se os preâmbulos forem iguais. Se
  precisar configurar, então passe o argumento -m para lib/previewframe.py ou
  modifique o arquivo diretamente.
* python3 deve estar no PATH do sistema.
