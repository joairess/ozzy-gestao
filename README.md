# Ozzy Gestão

Sistema web para a **Delícias da Ozzy**, delivery de açaí em Cruz das Armas (João Pessoa/PB). Os pedidos chegam pelo iFood e pelo WhatsApp. Só os do iFood ficavam registrados no aplicativo; os do WhatsApp eram anotados à mão. No fim do dia, conferir os dois canais e o caixa levava de 40 minutos a 1 hora, e não havia controle do estoque de insumos (polpa, complementos e embalagens).

O Ozzy Gestão reúne, num único lugar:

1. o registro dos pedidos dos dois canais;
2. o fechamento do dia, por canal e por forma de pagamento;
3. o estoque de insumos, com alerta quando a quantidade chega no mínimo.

É o MVP da Experiência Prática III. A aplicação é monolítica e segue o padrão **MVT** do Django: modelos, views e templates. As telas foram pensadas para a proprietária usar no celular, no balcão: letra grande, contraste alto e botões largos.

Os clientes dos dados de demonstração são fictícios (`Cliente Ana`, `Cliente Bruno`, `Cliente Carla`, `Cliente Diego`). O pedido guarda somente o nome — sem telefone e sem endereço.

## Funcionalidades

A navegação tem três telas, todas com login:

| Tela | O que faz |
| --- | --- |
| Novo pedido | Canal (iFood ou WhatsApp), nome do cliente, quantidades e forma de pagamento (Pix, dinheiro, cartão ou pago no iFood). O botão é **Registrar pedido**. O total é calculado no servidor pelo preço do cardápio. |
| Fechamento do dia | Total do dia, totais por canal e por pagamento, quantidade de pedidos e ticket médio. A pessoa informa o **valor conferido em caixa** e aperta **Fechar o dia**. |
| Estoque | Lista de insumos, aviso **Acabando** quando a quantidade atual é menor ou igual ao mínimo, e botões **Entrada** e **Saída**. |

O cadastro de produtos e insumos também pode ser feito no admin: <http://127.0.0.1:8000/admin/>, com o mesmo usuário de demonstração.

## Tecnologias

| Camada | Escolha |
| --- | --- |
| Linguagem | Python 3.12 |
| Back-end e templates | Django (MVT) |
| Interface | HTML, CSS e Bootstrap 5 |
| Banco em desenvolvimento | SQLite (`db.sqlite3`) |
| Banco quando existe `DATABASE_URL` | PostgreSQL |
| Testes | pytest e pytest-django |
| Integração contínua | GitHub Actions |

O Django traz login com senha em hash (PBKDF2), proteção CSRF, escape de HTML nos templates e ORM (consultas parametrizadas).

## Como rodar localmente

É preciso ter Python 3.12 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Abra <http://127.0.0.1:8000/>. O comando `seed_demo` cria o usuário de demonstração **somente na primeira execução**:

| Usuário | Senha |
| --- | --- |
| `ozzy` | `acai-demo-2026` |

Para usar outra senha nessa primeira criação, defina `DEMO_PASSWORD` no `.env` antes de rodar o seed. Essa senha é só da demonstração. Não use em produção e não coloque senha real no Git: o `.env` está no `.gitignore`. O arquivo versionado é o `.env.example`.

Sem `DATABASE_URL`, o Django usa o SQLite. Para PostgreSQL:

```bash
DATABASE_URL=postgres://usuario:senha@localhost:5432/ozzy_gestao python manage.py migrate
```

O esquema aceito é `postgres://` ou `postgresql://`. O parâmetro `sslmode` (por exemplo `?sslmode=require`) é repassado ao driver.

`DJANGO_DEBUG=1` é o padrão local, para o `runserver` entregar o CSS. Em produção, use `DJANGO_DEBUG=0`.

## Testes

```bash
pytest
```

A suíte cobre:

- modelos (alerta de estoque no mínimo, pedido sem telefone ou endereço);
- cálculo do pedido, movimentação de estoque e divergência do fechamento;
- telas com login obrigatório, CSRF, registro de pedido, fechamento e estoque;
- carga idempotente dos dados fictícios;
- leitura de `DATABASE_URL` e contraste das cores da interface.

## Integração contínua

O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda `pytest` com Python 3.12 em todo **push** e em todo **pull request**.

[![Testes](https://github.com/joairess/ozzy-gestao/actions/workflows/ci.yml/badge.svg)](https://github.com/joairess/ozzy-gestao/actions/workflows/ci.yml)

## Regras de negócio

O “hoje” usa o fuso `America/Fortaleza` (João Pessoa).

- **Total do pedido:** soma de `preço × quantidade` dos itens com quantidade maior que zero. Quantidade zero é ignorada. É preciso haver pelo menos um item. O subtotal fica gravado no item, então uma mudança futura de preço não reescreve o pedido.
- **Ticket médio:** total do dia dividido pela quantidade de pedidos, arredondado para centavos (meio para cima).
- **Divergência:** valor conferido em caixa menos o total dos pedidos do dia. Negativo significa que entrou menos dinheiro do que o sistema registrou; positivo, que sobrou. O botão **Fechar o dia** grava esses números. O mesmo dia não é fechado duas vezes.
- **Estoque:** entrada soma e saída diminui. A saída é recusada se o saldo ficaria negativo. O insumo aparece como **Acabando** quando a quantidade atual é menor ou igual ao estoque mínimo.

## Acessibilidade

A usuária principal tem 56 anos e usa o sistema no balcão. Por isso:

- texto com no mínimo 18px (`1.125rem`) e botões com altura mínima de 52px (`3.25rem`);
- contraste de texto no nível AA do WCAG 2.1 (as combinações de cor estão cobertas por teste);
- rótulos visíveis, foco visível e um link “Ir para o conteúdo”;
- o estado de estoque baixo não depende só da cor: o texto diz **Acabando**.
- Depois da validação no balcão (Estoque e Pedidos), o selo **Acabando** ficou maior e uma frase acima da lista explica que ele vale quando a quantidade é menor ou igual ao mínimo.

## Segurança

- Todas as telas do sistema exigem login. A senha fica só como hash.
- Os formulários enviam o token de CSRF do Django. Sair também é um POST com esse token.
- Não há segredo real no repositório. `DJANGO_SECRET_KEY` e `DATABASE_URL` ficam no ambiente.
- Com `DJANGO_DEBUG=0`, os cookies de sessão e de CSRF são marcados como seguros (HTTPS).

## Fora do escopo

- Integração automática com a API do iFood.
- Pagamento online e nota fiscal.
- Aplicativo para o cliente final fazer o pedido.

Cardápio, estoque e pedidos criados por `seed_demo` são inventados para a disciplina. Não representam vendas reais.
