# Gerador de Faca – Sacola Triangular

**Primacor** | Geração automática de faca para sacola triangular em SVG e PDF, escala 1:1.

## Visão Geral

O projeto gera **duas peças** que, montadas, formam a sacola triangular:

| Peça | Descrição |
|------|-----------|
| **CORPO** | Tira única com 5 painéis: `aba \| frente(A) \| lado(B) \| trás(A) \| aba`. As duas abas (B/2) formam o 2º lado e levam as aberturas da alça. |
| **FUNDO** | Duas peças idênticas espelhadas (separadas por linha de corte central), cada uma com aba de cola, vincos diagonais e aba superior. |

### Projeto fechado
O gerador aceita apenas **três medidas principais** (A, B, H) e calcula tudo automaticamente:

```
A  =  largura frente / trás  (mm)
B  =  largura do lado         (mm)
H  =  altura da sacola        (mm)
```

## Requisitos

- Python 3.9+
- `reportlab` para geração de PDF:
  ```bash
  pip install reportlab
  ```

## Uso rápido

```bash
# Medidas padrão (A=300, B=150, H=400)
python gerador_sacola_triangular.py

# Projeto personalizado
python gerador_sacola_triangular.py --A 350 --B 180 --H 420

# Com nome de saída
python gerador_sacola_triangular.py --A 350 --B 180 --H 420 --saida output/minha_sacola

# Só SVG (sem PDF)
python gerador_sacola_triangular.py --A 300 --B 150 --H 400 --so-svg

# Sem moldura da chapa
python gerador_sacola_triangular.py --A 300 --B 150 --H 400 --sem-moldura
```

## Todos os parâmetros

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `--A` | 300 | Largura frente/trás (mm) |
| `--B` | 150 | Largura do lado (mm) |
| `--H` | 400 | Altura da sacola (mm) |
| `--aba` | B/2 | Largura de cada aba da alça |
| `--raio` | 25 | Raio dos cantos arredondados |
| `--alca-larg` | 25 | Largura da abertura da alça |
| `--alca-alt` | 90 | Altura da abertura da alça |
| `--saida` | `sacola_triangular` | Prefixo dos arquivos de saída |
| `--sem-moldura` | — | Omite a moldura da chapa |
| `--fundo-manual` | — | Desativa cálculo automático do fundo |
| `--so-svg` | — | Gera apenas o SVG |

### Ajuste fino do fundo (modo manual)

Passe `--fundo-manual` junto com qualquer combinação de:

```
--fundo-larg, --fundo-dobra-larg, --fundo-cintura,
--fundo-dobra-y, --fundo-aba-alt, --fundo-aba-recuo,
--ombro-y, --lado-x, --lado-y0, --cola-y, --cola-x
```

## Cores (padrão gráfico)

| Camada | CMYK | Uso |
|--------|------|-----|
| **CORTE** | 0/100/100/0 | Vermelho – linha de corte |
| **VINCO** | 100/0/100/0 | Verde – vincos / dobras |
| **MOLDURA** | 0/50/50/50 | Cinza-bege – limite da chapa |

## Saída

São gerados dois arquivos por execução:
- `<saida>.svg` – vetor editável em Illustrator / Inkscape
- `<saida>.pdf` – 1:1 em mm, pronto para impressão / corte CNC

## Estrutura do projeto

```
gerador-sacola-triangular/
├── gerador_sacola_triangular.py   # script principal
├── output/                        # arquivos gerados
└── README.md
```
