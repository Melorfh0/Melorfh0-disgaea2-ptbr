# Disgaea 2 PC — Tradução PT-BR (projeto comunitário)

Projeto de tradução e pesquisa de compatibilidade para **Disgaea 2 PC**. A ideia é compartilhar ferramentas e documentação, reunir relatos de jogadores e melhorar a tradução em conjunto.

Repositório: [`Melorfh0/Melorfh0-disgaea2-ptbr`](https://github.com/Melorfh0/Melorfh0-disgaea2-ptbr).

> Projeto de fãs, sem afiliação com Nippon Ichi Software, NIS America, Steam ou Valve. É necessário possuir uma cópia legítima do jogo. Este repositório não distribui arquivos originais do jogo.

## Estado atual

A versão experimental local já reúne:

- Diálogos dos 18 arquivos `talk` disponíveis: `talk01`–`talk14` e `talk17`–`talk20`.
- Menus e interface: 937 de 1.097 formas catalogadas têm tradução na versão local; ainda há telas e rótulos que precisam de confirmação contextual.
- 603 descrições de itens, 369 linhas de ajuda/status de personagens e 367 descrições de habilidades.
- Abreviações dos meses localizadas no executável do clone.
- Vídeo de abertura com o texto inicial e a música japonesa legendados em português. O áudio original foi preservado e a reprodução foi confirmada em tela cheia no clone.

A versão foi testada em um clone local do jogo. A campanha carregou com o candidato das descrições de habilidades ativado, mas essas descrições não foram abertas individualmente para confirmação visual; a contagem traduzida não deve ser confundida com revisão de cada tela. O pacote final contém arquivos do jogo e, por isso, **não está anexado a este repositório**. Estamos preparando um formato de patch que trabalhe sobre os arquivos da cópia do próprio jogador. Até esse patch estar pronto, o GitHub servirá para acompanhar o projeto e organizar a participação da comunidade; ainda não há download público para instalar e testar no jogo.

## Ferramentas

- [`talk_dat_tool.py`](tools/talk_dat_tool.py): extrai candidatos de texto UTF-8 e substitui campos de mesmo tamanho em bytes. A opção de redimensionar continua experimental; o programa não é um reconstrutor completo de arquivos e pacotes.
- [`analyze_dat.py`](tools/analyze_dat.py): analisa os arquivos `talk`, inventaria candidatos de texto e faz um teste de reconstrução em cópia.
- [`inventory_cutscene_video_assets.py`](tools/inventory_cutscene_video_assets.py): inventaria arquivos de vídeo e dados de mídia presentes em uma instalação de teste fornecida pelo usuário.
- `ffmpeg` e `ffprobe`: usados localmente para queimar legendas no vídeo e verificar áudio/vídeo. Não são distribuídos aqui.
- SHA-256: usado para conferir cópias, versões e backups.

Os utilitários são ferramentas de pesquisa: alguns esperam uma estrutura local de pastas e exigem arquivos do jogo que não acompanham este repositório. Consulte [`TOOLS.md`](TOOLS.md) antes de executá-los.

## Convenções da tradução

As decisões de nomes, termos e estilo ficam em [`GLOSSARIO.md`](GLOSSARIO.md). Entre elas: Adell é tratado no masculino; `Overlord`, `Netherworld`, locais e nomes de itens do jogo permanecem em inglês; `ATK`, `DEF`, `INT`, `HIT`, `RES`, `SPD`, `LV` e classes também permanecem como no original. `Yes` vira `Sim` somente nos menus; `No` permanece `No`.

## O que falta

- Preparar e validar um patch que não inclua os arquivos completos do jogo.
- Testar o instalador do patch em uma cópia limpa e em diferentes configurações.
- Revisar os seis rótulos de interface que ainda precisam de contexto visual.
- Corrigir erros de tradução encontrados durante o jogo.
- Localizar e avaliar outras cutscenes; por enquanto, somente a abertura recebeu legendas.
- Continuar investigando limites de tamanho, acentos e espaçamento depois de priorizar uma versão funcional.

## Como participar

Entre no [servidor do Discord](https://discord.com/invite/XsCrHtVHFp) para acompanhar os testes e combinar a participação. Os relatos poderão ser enviados pelas [Issues](https://github.com/Melorfh0/Melorfh0-disgaea2-ptbr/issues/new/choose) ou pelo Discord.

Antes de abrir um relato, inclua:

- versão do jogo e idioma;
- área, capítulo, menu ou habilidade em que ocorreu;
- passos para reproduzir;
- texto esperado e texto exibido;
- captura de tela, se ajudar.

Não anexe executáveis, vídeos, arquivos `.DAT`, saves ou outros arquivos extraídos do jogo nas Issues.

## Licença e direitos

O arquivo [`LICENSE`](LICENSE) aplica a licença MIT somente às três ferramentas próprias listadas nele. Ela não cobre arquivos do jogo nem materiais de tradução. O conteúdo atual é um rascunho de documentação e ferramentas; ainda não publica o patch nem os arquivos de tradução do jogo.

