# Ozzy Gestão

Sistema web para a **Delícias da Ozzy**, delivery de açaí em Cruz das Armas (João Pessoa/PB). A proprietária recebe pedidos pelo iFood e pelo WhatsApp. Só os do iFood ficam registrados no aplicativo; os do WhatsApp eram anotados à mão. No fim do dia, conferir os dois canais e o caixa levava de 40 minutos a 1 hora, e o estoque de insumos (polpa, complementos e embalagens) não tinha controle.

O Ozzy Gestão junta, num único lugar:

1. o registro dos pedidos dos dois canais;
2. o fechamento do dia, por canal e por forma de pagamento;
3. o estoque de insumos, com alerta quando a quantidade chega no mínimo.

Este repositório é o MVP da Experiência Prática III. A modelagem segue o desenho da fase anterior: aplicação monolítica no padrão **MVT** do Django (modelos, views e templates).

Os nomes de clientes nos dados de demonstração são fictícios (`Cliente Ana`, `Cliente Bruno` e outros). O pedido guarda somente o nome — sem telefone e sem endereço.

## Tecnologias

| Camada | Escolha |
| --- | --- |
| Linguagem | Python 3.12 |
| Back-end e templates | Django (MVT) |
| Interface | HTML, CSS e Bootstrap 5 |
| Banco em desenvolvimento | SQLite |
| Banco quando `DATABASE_URL` existe | PostgreSQL |
| Testes | pytest e pytest-django |
| Integração contínua | GitHub Actions |

O Django já traz login com senha armazenada em hash (PBKDF2), proteção contra CSRF, escape de HTML nos templates e ORM (consultas parametrizadas).

## Como rodar localmente

Requisitos: Python 3.12 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Abra <http://127.0.0.1:8000/>.

O comando `seed_demo` cria o usuário de demonstração **somente na primeira vez**:

| Usuário | Senha |
| --- | --- |
| `ozzy` | `acai-demo-2026` |

A senha pode ser trocada com a variável `DEMO_PASSWORD` antes do primeiro `seed_demo`. Ela vale só para a demonstração local. Não use essa senha em produção e não coloque senha real no Git: use o arquivo `.env`, que está no `.gitignore`. O modelo versionado é o `.env.example`.

Sem `DATABASE_URL`, o banco é o arquivo `db.sqlite3`. Para PostgreSQL:

```bash
DATABASE_URL=postgres://usuario:senha@localhost:5432/ozzy_gestao python manage.py migrate
```

O esquema aceito é `postgres://` ou `postgresql://`. O parâmetro `sslmode` (por exemplo `?sslmode=require`) é repassado ao driver.

Neste incremento o admin em <http://127.0.0.1:8000/admin/> já mostra produtos, pedidos, insumos e fechamentos (mesmo usuário de demonstração). As telas do balcão — novo pedido, fechamento e estoque — entram no incremento seguinte.

## Regras de negócio

- **Novo pedido** — canal (iFood ou WhatsApp), nome do cliente, produtos e quantidades, forma de pagamento (Pix, dinheiro, cartão ou pago no iFood) e total calculado no servidor. O botão da tela é **Registrar pedido**.
- **Fechamento do dia** — total geral, totais por canal e por pagamento, quantidade de pedidos e ticket médio (total dividido pela quantidade, arredondado para centavos). A pessoa informa o **valor conferido em caixa**. A divergência é esse valor menos o total dos pedidos do dia: negativo quer dizer que entrou menos do que foi registrado. O botão **Fechar o dia** grava essa fotografia; o dia não é fechado duas vezes.
- **Estoque** — lista de insumos, destaque quando a quantidade atual é menor ou igual ao mínimo, e registro de entrada ou saída. A saída não deixa o saldo ficar negativo.

O fuso usado para “o dia” é `America/Fortaleza` (João Pessoa).

## Testes

```bash
pytest
```

Os testes cobrem os modelos, o cálculo de pedido, a movimentação de estoque, o resumo e a divergência do fechamento, a leitura de `DATABASE_URL` e a carga idempotente dos dados fictícios.

## Segurança

- Todas as telas do sistema exigem login. A senha fica só como hash.
- Os formulários usam o token de CSRF do Django.
- Não há segredo real no repositório. `DJANGO_SECRET_KEY` e `DATABASE_URL` ficam no ambiente.
- Em produção, defina `DJANGO_DEBUG=0`. Com debug desligado, os cookies de sessão e de CSRF são marcados como seguros (HTTPS).

## Fora do escopo

- Integração automática com a API do iFood.
- Pagamento online e nota fiscal.
- Aplicativo para o cliente final fazer o pedido.

## Licença dos dados de exemplo

Cardápio, estoque e pedidos criados por `seed_demo` são inventados para a disciplina. Não representam vendas reais.
