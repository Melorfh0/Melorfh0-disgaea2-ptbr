# Ferramentas e execução local

Os comandos abaixo são para pesquisa local com arquivos de uma cópia legítima do jogo. Não coloque arquivos do jogo neste repositório nem os envie em Issues.

As três ferramentas deste diretório estão sob a licença MIT, conforme o escopo descrito em [`LICENSE`](LICENSE). A licença não cobre dados do jogo nem textos de tradução.

## `talk_dat_tool.py`

Dependência: Python 3. Usa somente a biblioteca padrão.

```text
python tools/talk_dat_tool.py extract caminho\talk01.dat caminho\talk01.jsonl
python tools/talk_dat_tool.py rebuild caminho\talk01.dat traducoes.jsonl talk01_test.dat
```

O modo padrão só aceita texto traduzido com o mesmo comprimento em bytes UTF-8 do campo original. `--allow-resize` é experimental e não atualiza metadados externos desconhecidos; não use para substituir arquivos do jogo sem fazer cópias e validar o resultado.

## `analyze_dat.py`

Coloque cópias dos arquivos `talk*.dat` em `tools/inputs/` e execute:

```text
python tools/analyze_dat.py
```

O relatório e os arquivos de análise são criados em `tools/analysis/`. A rotina de teste cria um arquivo separado e não edita os arquivos de entrada.

## `inventory_cutscene_video_assets.py`

Espera uma pasta `work/game_probe/` contendo uma cópia de teste do jogo e grava um inventário em `outputs/cutscene_video_asset_inventory.json`. Ele lê nomes, tamanhos e assinaturas de mídia; não substitui vídeos.

## Ferramentas externas usadas no projeto

`ffmpeg` e `ffprobe` foram usados localmente para gerar e verificar a abertura com legendas queimadas. Eles não acompanham este repositório. A montagem do vídeo final atual ainda não foi convertida em um instalador público.

