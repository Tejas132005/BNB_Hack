# NeutraYield AI: Institutional Yield Automation 🚀
### AI-Powered Market-Neutral Yield Engine for BNB Chain

**Built for the BNB Hackathon | Professional Web3 Trading Infrastructure**

---

## 📖 Overview
**NeutraYield AI** is a professional-grade execution platform designed to capture market-neutral yield through high-fidelity automation and autonomous AI reasoning. In the volatile DeFi landscape, traditional yield farming often exposes users to significant directional risk. 

NeutraYield solves this by integrating a **quantitative strategy engine** with **Large Language Models (LLMs)** to identify, analyze, and execute delta-neutral, arbitrage, and yield rotation strategies. By separating **transaction preparation (backend)** from **transaction signing (client-side MetaMask)**, we maintain a strictly **non-custodial architecture** where the platform never touches user private keys.

---

## 🌟 Key Features

### 📡 Market Intelligence Layer
- **Dynamic MarketDataEngine**: Reactive synthetic data engine refreshing every 10 seconds to simulate high-frequency market shifts.
- **Advanced MarketAnalyzer**: Real-time calculation of RSI, MACD crossovers, volatility clustering, and funding rate arbitrage logic.

### 🛡️ Strategy Layer
- **Delta-Neutral Engine**: Active net delta tracking with automated hedge triggers to neutralize directional exposure.
- **Yield Rotation Engine**: Dynamic scoring of APY vs. Risk across multiple liquidity pools with automated allocation tracking.
- **Arbitrage Engine**: Sub-second spread detection across synthetic DEX pairs integrated directly with the execution flow.

### 📈 Risk Engine
- **Institutional Metrics**: Real-time calculation of Sharpe Ratio, Maximum Drawdown, and Volatility.
- **Equity Curve Tracking**: Live performance visualization and leverage monitoring to prevent liquidations.

### 🤖 AI Reasoning Layer (LLM)
- **Groq Llama-3 Integration**: High-speed inference mapping live market signals to plain-English strategy reasoning.
- **Structured JSON Output**: AI decisions are parsed into structured data for the execution layer while providing human-readable risk summaries.

### 🦊 Execution & Security Layer
- **Non-Custodial Signing**: Backend prepares unsigned transactions; users sign via MetaMask in their browser.
- **BNB Testnet Restriction**: Built-in enforcement for Chain ID 97 (BNB Testnet) to ensure safety and hackathon compliance.
- **Zero Private Key Storage**: The system architecture is designed so that private keys never leave the user's device.

### 📱 Telegram Bot Integration
- **Hybrid Interface**: A fully functional Telegram bot built with `python-telegram-bot`.
- **On-the-Go Scanning**: Trigger market scans and AI analysis directly from Telegram.
- **Actionable Buttons**: Buy / Sell / Stop / Limit execution triggers that redirect to the secure web interface for signing.

---

## 🏗️ System Architecture

1. **User Interaction**: Users access the system via the **Web Dashboard** (React/Django) or the **Telegram Bot**.
2. **Backend Services**: The **Django Backend** orchestrates the Market Data, Strategy, and Risk engines.
3. **AI Layer**: Live signals are passed to **Groq (Llama-3)** for strategy validation and risk insights.
4. **TX Preparation**: Once a strategy is triggered, the backend generates an unsigned transaction payload.
5. **Client Signing**: The user reviews the trade and signs the transaction using **MetaMask** (or mobile wallet).
6. **On-Chain Execution**: Signed transactions are broadcast to **BNB Testnet (Chain ID 97)**.
7. **Settlement & Logging**: Post-execution, the hash is verified on **BscScan**, and logs are updated in **TradeLog** and **AIActivityLog**.

---

## 🔄 Updated Flow Diagram

```text
      User (Web Interface)               User (Telegram Bot)
               |                                  |
               |---------- Market Scan -----------|
               |                 |                |
               |<------- Signal + AI Reasoning ---|
               |                                  |
               |------- Strategy Trigger ---------|
               |                 |                |
               |---------- Prepare TX ------------|
               |                 |                |
               |<------- Execution Link ----------|
               |                 |                |
     [ MetaMask Signing (Client-Side) ] <---------+
               |
     [ BNB Testnet (Chain ID 97) ]
               |
     [ Transaction Hash / BscScan ]
               |
     [ Portfolio + Risk Update ]
               |
     [ AIActivityLog + Dashboard ]
```

---

## 🤖 Telegram Bot Workflow
- **/start**: Initializes the session and triggers an immediate market scan.
- **Inline Keyboard UX**: Interactive buttons allow users to toggle between detailed AI analysis and direct trade preparation.
- **Secure Redirection**: Since Telegram environments are not suitable for private key entry, the bot provides a unique "Execution Link" that opens the Web Dashboard with the transaction pre-loaded for MetaMask signing.
- **Non-Custodial Enforcement**: Maintains the same security standard as the web app—zero backend signing.

---

## 🛠️ Tech Stack
- **Backend**: Django & Django REST Framework (Python)
- **AI Inference**: Groq SDK (Llama-3 models)
- **Blockchain**: Web3.py & BNB Chain Testnet (Chain ID 97)
- **Telegram**: python-telegram-bot (v20+)
- **Database**: SQLite3 (Optimized for persistent session tracking)
- **Frontend**: HTML5 / Bootstrap / Vanilla JS (MetaMask Integration)

---

## 🔒 Security Model
- **MetaMask Verification**: Every transaction requires a cryptographic signature from the user's local wallet.
- **Network Guard**: The platform strictly validates the network and rejects any transaction not aimed at Chain ID 97.
- **Error Handling**: Robust try/catch blocks for RPC failures, gas estimation issues, and wallet rejections.
- **No Persistence of Keys**: Neither the `.env` nor the database ever stores sensitive wallet credentials.

---

## 🚀 Future Improvements (Post-Hackathon)
- **Smart Contract Vaults**: Moving from EOA-based execution to proxy-vault contracts for complex multi-leg strategies.
- **PostgreSQL Migration**: Scaling the data engine for higher frequency logging and analytics.
- **Cross-Chain Expansion**: Integrating BNB Greenfield for decentralized storage of AI activity logs.
- **Async Workers**: Implementing Celery for background strategy monitoring and automated "emergency stop" signals.

---

## 🏃 How to Run

### 1. Prerequisites
- Python 3.10+
- MetaMask browser extension
- BNB Testnet added (Chain ID 97)
- tBNB for gas (from [BNB Faucet](https://testnet.bnbchain.org/faucet-smart))

### 2. Setup
```bash
# Clone the repository
git clone <repo_url>
cd BNB_Hack

# Install dependencies
pip install -r requirements.txt

# Initial Database Setup
python manage.py makemigrations
python manage.py migrate
```

### 3. Environment Configuration
Create a `.env` file based on `.env.example`:
```env
SECRET_KEY=your_secret
GROQ_API_KEY=your_groq_key
BNB_TESTNET_RPC=https://data-seed-prebsc-1-s1.binance.org:8545/
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 4. Running the Platform
```bash
# Terminal 1: Web Dashboard
python manage.py runserver

# Terminal 2: Telegram Bot (Optional)
python telegram_bot/bot.py
```

Visit `http://localhost:8000` to access the full NeutraYield suite.

---

## 📄 License
All rights reserved. Developed for the BNB Chain Hackathon 2025.
