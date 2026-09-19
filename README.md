# Dethron

Entrega verificável de mensagens sobre [Reticulum](https://reticulum.network/) e
LXMF, com um harness que trata cada afirmação como algo a ser derrubado antes de
ser publicado.

> *Verifiable message delivery over Reticulum/LXMF, with an evidence harness. Every
> milestone document states its contract, its result, the controls that must fail,
> and its limits. Documents are in Portuguese; code and commit messages in English.*

## O que isto resolve

Entrega **garantida** é impossível sobre contato intermitente: se o destinatário
nunca aparece, nada o alcança. O que é possível é **verificável** — saber, com
prova criptográfica e sem confiar no relé, em que estado uma mensagem está:

| Estado | Prova |
| --- | --- |
| **Entrou** | O relé assina uma custódia daquela mensagem, para aquele destinatário. Um relé que atesta e não entrega **é nomeado** |
| **Pendente** | Distinguindo *aguardando contato* de *atestado e não entregue* — pendência localizável, não um silêncio |
| **Saiu** | O destinatário assina um recibo que volta à origem, mesmo que origem e destino nunca estejam online juntos |

## O que está provado

Cada linha tem documento, controles que precisam falhar, limites declarados e
[artefato publicado](window/evidence/README.md):

- **[V1](window/V1_CUSTODY.md)** — custódia assinada, prova de entrada, pendência
  localizável, e [recibo de volta](window/V1_RECEIPT_RETURN.md).
- **[V2](window/V2_REPRODUCTION.md)** — reprodução em máquina independente,
  seguindo só o documento.
- **[V3c](window/V3C_BENCH.md)** — um objeto de 16 KiB atravessou entre duas
  máquinas por um enlace **que não carrega IP**, com o destinatário provado sem
  nenhuma interface IP, e as máquinas provadas distintas.

O índice completo, de G0 a V3, está em [window/](window/README.md). O
[plano mestre](DETHRON_MASTER_PLAN.md) traz hipóteses, critérios e o que foi
abandonado — inclusive o G2, encerrado **sem vantagem geral**, registrado como tal.

## O que ainda não existe

Isto é um harness com evidência, não um produto. Honestamente:

- **Não há cliente.** Os nós são dirigidos por bancadas. Ninguém instala e manda
  uma mensagem.
- **Escala nunca medida.** Uma mensagem, um relé, um destinatário, 16 KiB.
- **Só Windows.** Nunca rodou em Linux nem Android.
- **Chaves de laboratório.** Não há troca de chaves nem descoberta de contatos.
- **Sem modelo de ameaça escrito.** Os testes cobrem casos; falta o documento.

## Verificar

```powershell
python -m venv window/.venv-gateway
window/.venv-gateway/Scripts/python.exe -m pip install -r window/requirements-gateway.txt
window/.venv-gateway/Scripts/python.exe window/run_v2_reproduction.py --fast-only
```

Esperado: `ran=166 skipped=8 PASS`. O roteiro completo, incluindo as oito
reproduções reais, está em [V2_REPRODUCTION.md](window/V2_REPRODUCTION.md).

## Como este repositório trata evidência

- Um controle que **não pode** passar acompanha cada alegação. O `dark` do G4 já
  passou por acidente; o registro diz isso.
- Números vêm de artefatos, não de memória. Os artefatos citados estão publicados.
- O que falhou fica escrito. Cada documento tem uma seção de rodadas e verificações
  com os erros encontrados, inclusive os meus.
- Um defeito real do LXMF foi encontrado, reproduzido e corrigido: veja
  [window/upstream/](window/upstream/lxmf-stamp-zerodivision.md). A submissão à
  montante está bloqueada — o mantenedor se retirou e as *issues* estão desativadas.

## Licença

[Apache 2.0](LICENSE). O Reticulum e o LXMF são dependências sob suas próprias
licenças; este trabalho os importa, não os deriva.

## História

Este repositório contém trabalho anterior ao Dethron — sondas BitNet/Genesis,
*crates* Rust, um *worker* neural e um painel de navegador. Esse material saiu da
árvore em setembro de 2026 e **continua no histórico do git**, recuperável por
quem quiser.
