> 🎥 **Vídeo de até 3 minutos:** [INSERIR AQUI O LINK PÚBLICO DO GOOGLE DRIVE]

# Recomendação de investimento em short stay — Itapema (SC)

Análise do mercado de Airbnb e de imóveis à venda em Itapema para responder onde e em qual perfil a Seazone deveria investir.

## Decisão em uma frase

**Eu não compraria um imóvel pelo preço mediano anunciado.** Se a decisão estratégica exigir uma aquisição, priorizaria um **apartamento pronto de 2 quartos em Morretes**, com vaga e estrutura voltada a famílias, mas somente após validar o calendário real e negociar um desconto relevante. **Meia Praia é a melhor localização para faturamento; Morretes oferece o melhor equilíbrio entre receita, ticket e volume de evidência.**

## Respostas às quatro perguntas

1. **Melhor perfil:** apartamento de 2 quartos para investimento ajustado a risco. Unidades de 4 quartos têm a maior receita bruta, mas o preço de compra reduz fortemente o yield. Apartamentos dominam a oferta e oferecem amostra muito mais confiável que casas.
2. **Melhor localização em receita:** Meia Praia. Na amostra estrita, a receita proxy mediana em 90 dias é de **R$ 16,1 mil**, contra **R$ 12,3 mil** em Morretes e **R$ 10,9 mil** no Centro. A liderança se repete nas três capturas de preço.
3. **Características associadas às maiores receitas:** acesso/proximidade de praia, operação Superhost, maior capacidade de hóspedes, mais banheiros e experiência/reputação do anfitrião. O modelo explica apenas 17,7% fora da amostra; as relações são associativas, não causais.
4. **O que comprar:** um 2 quartos pronto em Morretes, apenas com preço de entrada atrativo. O candidato indicativo de **R$ 458 mil** resulta em investimento total estimado de **R$ 590,9 mil** e yield líquido de **1,4% / 2,5% / 3,9%** nos cenários baixo/base/alto. Como o retorno operacional é baixo, a decisão-base é **negociar ou não comprar**.

### Posição sobre compactos no Centro

A tese de **studio/1 quarto no Centro não é sustentada** por esta base: o Centro perde para Meia Praia em receita, e o segmento de 1 quarto no Centro apresenta yield líquido base mediano de aproximadamente **0,9%**, abaixo do 2 quartos em Morretes (**1,6%**) e do 2 quartos em Meia Praia (**1,3%**).

## Estrutura do repositório

```text
.
├── ai-log/
│   └── conversa-completa.md
├── artefatos/
│   └── analise_investimento_itapema.xlsx
├── data/
│   └── cinco CSVs fornecidos no desafio
├── outputs/
│   └── analysis_results/
│       ├── analysis_metadata.json
│       ├── driver_model.csv
│       ├── investment_candidates.csv
│       ├── investment_segment_returns.csv
│       ├── strict_by_bedrooms.csv
│       └── strict_by_suburb.csv
├── src/
│   └── analyze_itapema.py
├── relatorio.md
└── requirements.txt
```

## Como rodar

Requisitos: Python 3.11 ou superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/analyze_itapema.py --data-dir data --output-dir outputs/analysis_results
```

O script aceita tanto os nomes originais quanto os nomes curtos:

| Base | Nome original | Alternativa |
|---|---|---|
| Detalhes Airbnb | `Details_Itapema.csv` | `details.csv` |
| Hosts | `Hosts_ids_Itapema.csv` | `hosts.csv` |
| Localização | `Mesh_Ids_Data_Itapema.csv` | `mesh.csv` |
| Preço/disponibilidade | `Price_AV_Itapema.csv` | `price.csv` |
| Venda | `VivaReal_Itapema.csv` | `vivareal.csv` |

A recomendação escrita está em [`relatorio.md`](relatorio.md). A planilha pronta para auditoria e alteração de premissas está em [`artefatos/analise_investimento_itapema.xlsx`](artefatos/analise_investimento_itapema.xlsx).

## Metodologia resumida

- A captura de 20/01/2025 é o corte principal, com horizonte de 90 dias.
- Uma noite ausente do arquivo de disponibilidade é tratada como **indisponível**, não automaticamente como reserva.
- A receita proxy soma o preço esperado das noites indisponíveis, usando um índice diário de preço construído dentro da própria captura.
- A amostra estrita exige pelo menos uma data disponível em cada bloco de 30 dias, reduzindo o risco de calendário fechado.
- As medianas recebem intervalo de confiança bootstrap.
- Os drivers são estimados em modelo log-linear com erros robustos e validação cruzada em cinco partes.
- O retorno cruza pares de Airbnb por bairro/quartos com preço pedido, condomínio e IPTU do VivaReal.

## Premissas do cenário-base

- 75% do run-rate de Jan–Abr para corrigir sazonalidade anual;
- 85% das noites indisponíveis reconhecidas como reservas;
- 33% da receita para gestão, canais e custos variáveis;
- 5% do preço para aquisição;
- setup/mobília de R$ 60 mil + R$ 25 mil por quarto;
- condomínio/IPTU ausentes ou com valores de portal implausivelmente baixos são imputados pela mediana do segmento.

Todas as premissas são editáveis na aba **Premissas** da planilha.

## Limitações decisivas

- Não há reservas nem faturamento realizado; receita e ocupação são proxies.
- Existem somente três capturas de preços, todas em janeiro de 2025.
- O VivaReal informa preço pedido, não preço transacionado.
- O cruzamento Airbnb–venda ocorre por pares de bairro e quartos, não por imóvel idêntico.
- Valorização imobiliária, financiamento, imposto de renda e custo de capital não entram no NOI.
- Antes de investir hoje, é obrigatório atualizar preços, convenção do condomínio e 12 meses de reservas reais.

## Contexto externo

A Seazone se descreve como uma proptech de gestão e investimento em aluguel por temporada, com tecnologia e dados no centro da operação ([Seazone — Quem somos](https://seazone.com.br/institucional/quem-somos)). Itapema tinha população estimada de 86.116 pessoas em 2025 ([IBGE](https://www.ibge.gov.br/cidades-e-estados/sc/itapema.html)). Em abril de 2026, o FipeZAP apontou preço médio anunciado de R$ 15.179/m² e alta de 8,10% em 12 meses ([FipeZAP](https://downloads.fipe.org.br/indices/fipezap/fipezap-202604-residencial-venda.pdf)). Em agosto de 2026, a meta Selic era 14,00% a.a., elevando o custo de oportunidade de um yield operacional abaixo de 4% ([Banco Central](https://www.bcb.gov.br/controleinflacao/historicotaxasjuros)).


