# preview-beamer-slide package

Faz um preview de um slide do beamer.


## Uso

1. Configure o comando para o previsualizador nas configurações do pacote
2. Coloque o cursor em qualquer linha do frame
3. Aperte ctl+alt+p (ou modifique o atalho)

### Observações

* Compila somente uma vez por eficiência (mesmo que haja referências resolvidas).
 Execute duas vezes no mesmo frame se for o caso.
* Usa pfdlatex; se precisar mudar, altere o arquivo lib/previewframe.py
* Se houver vários arquivos  \*.tex  com \\documentclass, então copia o preâmbulo
  de qualquer um. Não há problema se os preâmbulos forem iguais. Se precisar
  configurar, então passe o argumento -m para lib/previewframe.py ou modifique
  o arquivo diretamente.
* python3 deve estar no PATH do sistema
