# Relatório de recomendação de investimento — Itapema (SC)

**Data da decisão:** 26/08/2026  
**Data-base dos imóveis:** Airbnb 13–20/01/2025; VivaReal 11/01/2025  
**Objetivo:** identificar o perfil e a localização com melhor relação entre receita de short stay, evidência estatística e capital investido.

## Recomendação executiva

Minha recomendação é **não comprar aos preços medianos anunciados**. O mercado de Itapema entrega receita relevante, principalmente em Meia Praia, mas os preços de aquisição comprimem o yield operacional.

Se houver mandato estratégico para adquirir um ativo, eu escolheria um **apartamento pronto de 2 quartos em Morretes**, com vaga, boa capacidade para famílias, ar-condicionado, Wi-Fi, máquina de lavar e acesso simples à praia. O ativo deve ser comprado apenas com desconto e após diligência do calendário e do condomínio.

O racional é simples:

- Meia Praia é o melhor bairro para receita, mas tem aquisição mais cara;
- Morretes preserva parte da diária e da demanda com ticket menor;
- 2 quartos têm amostra robusta tanto no Airbnb quanto no VivaReal;
- 4 quartos faturam mais, porém geram yield muito inferior;
- 1 quarto no Centro não supera 2 quartos em eficiência nem em receita.

## 1. Dados, cobertura e definição de receita

| Base | Linhas | Cobertura relevante |
|---|---:|---|
| Detalhes Airbnb | 4.441 | 4.441 listings únicos |
| Hosts | 4.440 | 3.057 hosts; duplicação esperada por host com vários anúncios |
| Localização | 4.441 | 100% dos listings de detalhes |
| Preço/disponibilidade | 118.839 | 1.005 listings; capturas em 06, 07 e 20/01/2025 |
| VivaReal | 8.329 | 8.293 IDs únicos; preço pedido de venda |

A base não contém reservas confirmadas. Portanto:

> **Receita proxy de 90 dias = soma do preço esperado das noites ausentes no calendário observado.**

Uma noite ausente pode ser reserva, bloqueio do proprietário ou calendário não aberto. Para reduzir o viés:

1. o corte principal usa uma única captura, 20/01/2025;
2. a amostra estrita exige disponibilidade em cada bloco de 30 dias;
3. a anualização aplica desconto de sazonalidade;
4. somente 85% da indisponibilidade é reconhecida como reserva no cenário-base;
5. os rankings são comparados nas três capturas.

Dos 777 listings com noites futuras na captura principal, 588 entram na amostra estrita.

## 2. Qual é o melhor perfil?

### Receita bruta

| Quartos | N | Receita proxy mediana — 90d | IC bootstrap 95% | ADR mediana |
|---:|---:|---:|---:|---:|
| 4 | 38 | R$ 27,1 mil | R$ 22,1–34,2 mil | R$ 950 |
| 3 | 241 | R$ 16,6 mil | R$ 15,5–17,8 mil | R$ 662 |
| 2 | 201 | R$ 12,3 mil | R$ 11,2–13,4 mil | R$ 456 |
| 1 | 98 | R$ 9,9 mil | R$ 8,5–10,4 mil | R$ 427 |

**Leitura:** 4 quartos é o vencedor de faturamento, mas não de investimento. Em Meia Praia, o preço mediano de compra de um 4 quartos é R$ 3,5 milhões e o yield líquido base cai para aproximadamente 0,8%.

### Perfil recomendado

**Apartamento de 2 quartos** é a escolha ajustada a risco:

- 201 anúncios na amostra estrita da cidade;
- acomoda famílias sem exigir o capital de 3–4 quartos;
- 90 pares Airbnb em Meia Praia e 38 em Morretes;
- 241 ofertas comparáveis no VivaReal em Meia Praia e 1.031 em Morretes;
- maior liquidez analítica e menor risco de base pequena.

Apartamentos e casas têm receita mediana semelhante na amostra ampla, mas casas contam com apenas 33 observações, contra 737 apartamentos. A recomendação por apartamento é sustentada mais por escalabilidade, comparabilidade e liquidez do que por uma diferença estatística clara de faturamento.

## 3. Qual é a melhor localização em receita?

| Bairro | N | Receita proxy mediana — 90d | IC bootstrap 95% | Ocupação proxy |
|---|---:|---:|---:|---:|
| Meia Praia | 350 | R$ 16,1 mil | R$ 14,8–17,1 mil | 31,1% |
| Morretes | 52 | R$ 12,3 mil | R$ 10,7–15,4 mil | 29,4% |
| Centro | 147 | R$ 10,9 mil | R$ 10,0–12,3 mil | 25,6% |

Meia Praia supera o Centro em aproximadamente **48%** na mediana da amostra estrita. A liderança também aparece nas capturas de 6, 7 e 20 de janeiro, reduzindo o risco de a conclusão depender de um único dia.

**Resposta:** Meia Praia é a melhor localização em faturamento. Morretes é a melhor alternativa para eficiência de capital.

## 4. Quais características explicam as melhores receitas?

Foi estimado um modelo log-linear com 572 anúncios, controles de bairro e tipologia, erros robustos e validação cruzada em cinco partes.

| Característica | Impacto aproximado condicionado | Estatística t | Leitura |
|---|---:|---:|---|
| Acesso/proximidade de praia | +23,4% | 3,04 | sinal positivo robusto |
| Superhost | +25,0% | 2,95 | execução operacional importa |
| Capacidade de hóspedes | +16,0% por 1 desvio-padrão | 2,42 | grupos/famílias elevam receita |
| Banheiros | +11,3% por 1 desvio-padrão | 2,17 | conveniência para grupos |
| Reviews do host | +15,8% por 1 desvio-padrão log | 2,12 | reputação operacional |

O R² fora da amostra é **17,7%**. O modelo é útil para ordenar sinais, mas não para atribuir causalidade. Distância exata da praia, qualidade do prédio, vista, reforma, política de calendário e preço dinâmico provavelmente explicam boa parte do restante.

Não há evidência robusta de que anúncio profissional ou reserva instantânea, isoladamente, produzam maior receita. Comparações simples podem inclusive apontar o contrário por composição de portfólio.

## 5. Retorno por segmento

Premissas-base: 75% do run-rate sazonal, 85% da indisponibilidade reconhecida como reserva, 33% de custos variáveis, 5% de custos de aquisição e setup de R$ 60 mil + R$ 25 mil por quarto.

| Segmento | N Airbnb | N venda | Preço mediano | Receita anual bruta | NOI anual | Yield líquido |
|---|---:|---:|---:|---:|---:|---:|
| Tabuleiro, 2q | 10 | 109 | R$ 780 mil | R$ 32,2 mil | R$ 15,9 mil | 1,7% |
| **Morretes, 2q** | **38** | **1.031** | **R$ 790 mil** | **R$ 29,9 mil** | **R$ 15,0 mil** | **1,6%** |
| Meia Praia, 1q | 15 | 56 | R$ 877,5 mil | R$ 34,2 mil | R$ 13,2 mil | 1,3% |
| Meia Praia, 2q | 90 | 241 | R$ 1,07 mi | R$ 33,9 mil | R$ 15,6 mil | 1,3% |
| Centro, 2q | 47 | 84 | R$ 1,12 mi | R$ 32,6 mil | R$ 14,8 mil | 1,2% |
| Centro, 1q | 70 | 19 | R$ 890 mil | R$ 25,8 mil | R$ 9,5 mil | 0,9% |

Tabuleiro lidera numericamente, mas tem apenas 10 pares Airbnb e intervalo de receita amplo; não é a escolha de maior confiança. Morretes é o primeiro segmento com evidência alta e grande profundidade de mercado.

## 6. O que eu compraria

### Alvo indicativo

- Apartamento pronto, 2 quartos, Morretes;
- 52 m², 1 vaga;
- preço pedido no snapshot: **R$ 458 mil**;
- custo de aquisição: 5%;
- setup/mobília: R$ 110 mil;
- investimento total: **R$ 590,9 mil**;
- pares operacionais: 38 anúncios Airbnb de 2 quartos em Morretes;
- ADR mediana dos pares: R$ 449;
- ocupação proxy mediana: 27,2%.

| Cenário | Receita bruta anual | NOI anual | Yield líquido |
|---|---:|---:|---:|
| Baixo | R$ 19,7 mil | R$ 8,2 mil | 1,4% |
| Base | R$ 29,9 mil | R$ 15,0 mil | 2,5% |
| Alto | R$ 42,3 mil | R$ 23,3 mil | 3,9% |

O candidato é uma **referência de underwriting**, não uma ordem de compra: o anúncio é de janeiro de 2025 e pode não estar mais disponível.

### Preço máximo

Com NOI base de cerca de R$ 15 mil:

- para yield líquido de 3%, o preço máximo do imóvel seria aproximadamente **R$ 372 mil**;
- para yield líquido de 4%, o preço máximo seria aproximadamente **R$ 253 mil**.

Logo, o preço pedido de R$ 458 mil exige desconto de aproximadamente 19% para 3% de yield e 45% para 4%.

### Decisão

**No-go no preço pedido.** Eu avançaria apenas se a diligência revelar receita real acima do proxy, condomínio baixo e permitido para short stay, ou se a negociação trouxer o preço para perto de R$ 370 mil. Valorização patrimonial pode aumentar o retorno total, mas não foi projetada porque a base não contém transações nem série histórica suficiente.

## 7. Contexto de 2026

Itapema é um mercado caro: o FipeZAP indicou R$ 15.179/m² em abril de 2026 e valorização de 8,10% em 12 meses ([FipeZAP](https://downloads.fipe.org.br/indices/fipezap/fipezap-202604-residencial-venda.pdf)). Ao mesmo tempo, a meta Selic era 14,00% a.a. em agosto de 2026 ([Banco Central](https://www.bcb.gov.br/controleinflacao/historicotaxasjuros)).

Essa comparação não substitui uma análise de retorno total, mas reforça que um yield operacional de 1%–4% precisa de tese forte de valorização, uso estratégico ou aquisição com desconto.

## 8. Diligência antes de qualquer compra

1. Atualizar o preço pedido e obter três comparáveis transacionados.
2. Solicitar 12 meses de reservas, ADR, ocupação, cancelamentos e bloqueios de pares reais.
3. Confirmar que a convenção do condomínio permite short stay.
4. Medir distância a pé da praia e avaliar vista, ruído, acesso e estacionamento.
5. Orçar mobília, enxoval, ar-condicionado, fechadura e manutenção.
6. Validar condomínio, IPTU, escritura, incorporação e entrega.
7. Recalcular cenários na planilha antes do comitê de investimento.

## Conclusão final

- **Receita:** Meia Praia.
- **Perfil de maior faturamento:** apartamento de 4 quartos.
- **Perfil de melhor decisão de capital:** apartamento de 2 quartos.
- **Local para eficiência:** Morretes.
- **Compra recomendada hoje:** nenhuma no preço mediano; comprar somente com desconto e dados operacionais confirmados.
- **Tese de compactos no Centro:** rejeitada pela base analisada.


