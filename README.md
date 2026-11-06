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
| Banco em desenvolvimento e no Render gratuito | SQLite (`db.sqlite3`) |
| Banco quando existe `DATABASE_URL` | PostgreSQL (lido com dj-database-url) |
| Servidor de produção | gunicorn (`config.wsgi:application`) |
| Arquivos estáticos em produção | WhiteNoise, depois de `collectstatic` |
| Testes | pytest e pytest-django |
| Integração contínua | GitHub Actions |
| Hospedagem prevista | Render, web service no plano gratuito |

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

`DJANGO_DEBUG=1` é o padrão local, para o `runserver` entregar o CSS. Em produção, use `DJANGO_DEBUG=0`. No Render, se a variável não existir, o debug também fica desligado, porque a plataforma define `RENDER=true`.

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

## Publicação no Render (plano gratuito)

A Experiência Prática IV precisa de uma URL pública. O arquivo [`render.yaml`](render.yaml) descreve um único web service no plano **free**, sem banco pago. O Python fica na 3.12 pelo arquivo [`.python-version`](.python-version), porque o padrão atual da plataforma pode ser mais novo.

Depois que este Blueprint estiver na branch `main`, crie o serviço em:

<https://dashboard.render.com/blueprint/new?repo=https://github.com/joairess/ozzy-gestao>

O serviço acompanha a `main` (`autoDeployTrigger: commit`).

| Etapa | Comando |
| --- | --- |
| Build | `pip install -r requirements.txt && python manage.py collectstatic --noinput` |
| Start | `bash scripts/start.sh` |

O [`Procfile`](Procfile) repete o start. O script aplica as migrações, roda `seed_demo` e sobe o gunicorn escutando em `0.0.0.0:$PORT` (um worker):

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 1
```

O módulo WSGI é `config.wsgi:application`. A checagem de saúde é `GET /saude/`, que responde `200` com o texto `ok` e não pede login.

O WhiteNoise entrega o CSS. O `collectstatic` do build grava os arquivos em `staticfiles/`, com nome e compressão de produção, porque `DJANGO_DEBUG=0`.

### Variáveis de ambiente

O Blueprint já declara estas variáveis. `DJANGO_SECRET_KEY` é gerada pela plataforma (`generateValue`); não coloque a chave no Git.

| Variável | Valor no Blueprint | Para que serve |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | gerada no Render | Sessão e CSRF. Também aceita o nome `SECRET_KEY`. |
| `DJANGO_DEBUG` | `0` | Desliga o debug e marca os cookies como seguros. |
| `DJANGO_ALLOWED_HOSTS` | `.onrender.com` | Libera o subdomínio do serviço. O código também acrescenta `RENDER_EXTERNAL_HOSTNAME`. |
| `DEMO_PASSWORD` | `acai-demo-2026` | Senha só na primeira criação do usuário `ozzy`. |
| `DATABASE_URL` | ausente | Sem ela, o Django usa SQLite. |

O Render define sozinho `RENDER_EXTERNAL_URL` (por exemplo `https://ozzy-gestao.onrender.com`). Essa origem entra em `CSRF_TRUSTED_ORIGINS`, então o login e os formulários funcionam em HTTPS. Um domínio próprio precisa ser acrescentado em `DJANGO_ALLOWED_HOSTS` e em `DJANGO_CSRF_TRUSTED_ORIGINS`.

### Login da demonstração

| Usuário | Senha |
| --- | --- |
| `ozzy` | `acai-demo-2026` |

O mesmo usuário entra no admin em `/admin/`. A senha é a da disciplina, documentada de propósito. Não serve para um sistema com dados reais.

### Limites do plano gratuito

- Depois de **15 minutos sem acesso**, o serviço **adormece**. O próximo acesso leva cerca de **um minuto** para acordar. O Render mostra uma página de espera nesse intervalo.
- O disco é **efêmero**. Pedidos e estoque gravados na sessão somem quando o serviço adormece, reinicia ou recebe um deploy novo. Cada boot roda `migrate` e `seed_demo` de novo, então o usuário `ozzy` e os dados fictícios voltam. O que a proprietária lançou depois do último boot não volta.
- O plano gratuito não tem disco persistente nem SSH. Há um teto de **750 horas** de instância por mês no workspace; o tempo adormecido não conta.
- O Postgres gratuito da plataforma expira em 30 dias. Este MVP não o usa. Se no futuro existir um `DATABASE_URL` (`postgres://` ou `postgresql://`), o mesmo código passa a usá-lo, inclusive com `sslmode`, e o start continua rodando `migrate` no boot. O `preDeployCommand`, que migra antes de o processo novo receber tráfego, só existe em plano pago.

O redirecionamento de HTTP para HTTPS fica na borda do Render. O Django não liga `SECURE_SSL_REDIRECT`, porque a checagem de saúde chega ao processo por HTTP.

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

## Segurança

- Todas as telas do sistema exigem login. A senha fica só como hash.
- Os formulários enviam o token de CSRF do Django. Sair também é um POST com esse token.
- Não há segredo real no repositório. `DJANGO_SECRET_KEY` e `DATABASE_URL` ficam no ambiente. No Render a chave é gerada pela plataforma.
- Com `DJANGO_DEBUG=0`, os cookies de sessão e de CSRF são marcados como seguros (HTTPS). No Render o processo confia em `X-Forwarded-Proto`, porque o TLS termina na borda.

## Fora do escopo

- Integração automática com a API do iFood.
- Pagamento online e nota fiscal.
- Aplicativo para o cliente final fazer o pedido.

Cardápio, estoque e pedidos criados por `seed_demo` são inventados para a disciplina. Não representam vendas reais.
