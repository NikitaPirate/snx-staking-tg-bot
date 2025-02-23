# SNX Staking Monitoring Telegram Bot

A Telegram bot for monitoring SNX (Synthetix) staking positions across Ethereum and Optimism networks.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/NikitaPirate/snx-staking-tg-bot.git
cd snx-staking-tg-bot
```

2. Copy `env_example` to `.env` and fill in your values

3. Build and start the containers:
```bash
docker-compose build
docker-compose up -d
```

## Note

The application is developed and tested to work with:
- PostgreSQL
- Alchemy API

## License

[MIT](https://choosealicense.com/licenses/mit/)
