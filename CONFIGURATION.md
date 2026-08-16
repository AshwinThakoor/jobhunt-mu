# Configuration

Copy `.env.example` to `.env`. Never commit `.env`.

| Variable | Required | Default | Description |
|---|---:|---|---|
| `DJANGO_SECRET_KEY` | Production | insecure local fallback | Django signing secret; generate a unique long value |
| `DJANGO_DEBUG` | No | `true` | Must be `false` in production |
| `DJANGO_ALLOWED_HOSTS` | Production | `localhost,127.0.0.1` | Comma-separated hostnames |
| `DB_ENGINE` | No | `sqlite` | Set to `mysql` for configured MySQL support |
| `MYSQL_DATABASE` | MySQL | `internship` | Database name |
| `MYSQL_USER` | MySQL | `root` | Database user |
| `MYSQL_PASSWORD` | MySQL | empty | Database password |
| `MYSQL_HOST` | MySQL | `localhost` | Database host |
| `MYSQL_PORT` | MySQL | `3306` | Database port |
| `STRIPE_PUBLISHABLE_KEY` | Payments | empty | Test/live publishable key |
| `STRIPE_SECRET_KEY` | Payments | empty | Secret API key; never expose client-side |
| `STRIPE_WEBHOOK_SECRET` | Webhooks | empty | `whsec_...` signing secret |
| `PREMIUM_PRICE_CENTS` | No | `1999` | Integer amount in the currency's minor unit |
| `PREMIUM_CURRENCY` | No | `usd` | Lowercase ISO currency code |
| `JOOBLE_API_KEY` | Optional | empty | Approved Jooble API credential |
| `FREELANCER_OAUTH_TOKEN` | Optional | empty | Approved Freelancer API credential |

## Example local configuration

```dotenv
DJANGO_SECRET_KEY=replace-with-generated-secret
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
STRIPE_PUBLISHABLE_KEY=pk_test_replace_me
STRIPE_SECRET_KEY=sk_test_replace_me
STRIPE_WEBHOOK_SECRET=whsec_replace_me
PREMIUM_PRICE_CENTS=1999
PREMIUM_CURRENCY=usd
```

## Secret handling

Use GitHub Actions secrets, a cloud secret manager, or deployment-platform environment variables. Rotate a secret immediately if it appears in a commit, screenshot, log, issue, or chat.
