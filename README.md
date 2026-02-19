# Solana Cluster Monitoring Backend





A comprehensive FastAPI backend for real-time monitoring and detection of coordinated wallet clusters on the Solana blockchain. This system identifies parent wallets that fund multiple child wallets within short time windows, tracks their token trading activities, and provides detailed analytics for blockchain analysis.

## 🎯 Project Overview

This backend provides real-time on-chain monitoring capabilities for the Solana blockchain with the following core features:

- **Cluster Detection**: Identifies parent wallets funding 5+ child wallets within configurable time windows
- **Token Activity Tracking**: Monitors buy/sell activities of detected child wallets
- **Real-time Polling**: Continuously polls Solana transactions every 10-30 seconds
- **Helius API Integration**: Leverages Helius API for fast, decoded transaction data
- **RESTful API**: Provides comprehensive endpoints for frontend dashboard integration

### Use Cases
- **MEV Detection**: Identify coordinated market manipulation strategies
- **Bot Activity Monitoring**: Track automated trading patterns
- **Market Analysis**: Analyze coordinated buying/selling behaviors
- **Security Research**: Detect suspicious wallet clustering activities

## 🏗️ Project Structure

```
Solana-Cluster-Monitoring-Backend/
├── app/
│   ├── api/v1/                 # API version 1 endpoints
│   │   ├── endpoints/
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   └── wallets.py      # Wallet monitoring endpoints
│   │   └── api.py              # API router configuration
│   ├── core/                   # Core application components
│   │   ├── config.py           # Configuration management
│   │   ├── database.py         # Database connection setup
│   │   └── security.py         # Security utilities
│   ├── models/                 # SQLAlchemy database models
│   │   ├── parent_wallet.py    # Parent wallet model
│   │   └── child_wallet.py     # Child wallet model
│   ├── schemas/                # Pydantic request/response schemas
│   │   ├── wallet.py           # Wallet schemas
│   │   └── transaction.py      # Transaction schemas
│   ├── services/               # Business logic services
│   │   ├── helius_service.py   # Helius API integration
│   │   └── wallet_service.py   # Wallet detection logic
│   └── main.py                 # FastAPI application entry point
├── requirements.txt            # Python dependencies
├── test_api.py                # API testing script
└── README.md                  # This documentation
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**: Ensure you have Python 3.8 or higher installed
- **Helius API Key**: Sign up at [Helius](https://helius.xyz) for API access
- **Git**: For cloning the repository

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Solana-Cluster-Monitoring-Backend
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment** (optional):
   Create a `.env` file in the root directory:
   ```env
   HELIUS_API_KEY=your_helius_api_key_here
   DATABASE_URL=sqlite:///./app.db
   ENVIRONMENT=development
   DEBUG=True
   MIN_CHILD_WALLETS=5
   DETECTION_WINDOW_MINUTES=5
   ```

### Running the Application

1. **Start the development server**:
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Access the application**:
   - **API Documentation**: http://localhost:8000/docs
   - **Alternative Docs**: http://localhost:8000/redoc
   - **Health Check**: http://localhost:8000/health
   - **Root Endpoint**: http://localhost:8000/

The server will start on `http://localhost:8000` with auto-reload enabled for development.

## 📚 API Documentation

### Core Endpoints

#### Health Check
```http
GET /health
```
Returns the health status of the API.

**Response:**
```json
{
  "status": "healthy"
}
```

#### Raw Transactions
```http
GET /api/v1/wallets/raw-transactions/{wallet_address}
```
Fetches raw transaction data for a specific Solana wallet address.

**Parameters:**
- `wallet_address` (path): Solana wallet address

**Response:**
```json
{
  "transactions": [...] // Array of transaction objects
}
```

#### Cluster Detection
```http
GET /api/v1/wallets/cluster-detection/{wallet_address}
```
Detects wallet clusters where a parent wallet funds multiple child wallets.

**Parameters:**
- `wallet_address` (path): Parent wallet address to analyze
- `min_children` (query, optional): Minimum children required for cluster (3-20, default: 5)
- `funding_window` (query, optional): Funding window in minutes (1-30, default: 5)

**Response:**
```json
{
  "parent_wallet": "string",
  "cluster_type": "BUY_CLUSTER|SELL_CLUSTER",
  "child_wallets": [...],
  "total_sol_funded": 0.0,
  "coordination_score": 0.0
}
```

### Interactive API Documentation

Visit `http://localhost:8000/docs` when the server is running to explore the full interactive API documentation with:
- Complete endpoint specifications
- Request/response examples
- Try-it-out functionality
- Schema definitions

## 🧪 Testing

### Running API Tests

The project includes a comprehensive test script to verify all endpoints:

```bash
python test_api.py
```

This script tests:
- Health endpoint connectivity
- Raw transaction fetching
- Cluster detection functionality
- API documentation accessibility

### Manual Testing

You can also test individual endpoints using curl or any HTTP client:

```bash
# Health check
curl http://localhost:8000/health

# Raw transactions (replace with actual wallet address)
curl "http://localhost:8000/api/v1/wallets/raw-transactions/YourWalletAddressHere"

# Cluster detection with custom parameters
curl "http://localhost:8000/api/v1/wallets/cluster-detection/YourWalletAddressHere?min_children=3&funding_window=10"
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HELIUS_API_KEY` | Your Helius API key | `29dce386-f700-47b7-a61d-6562b1145a45` |
| `HELIUS_BASE_URL` | Helius API base URL | `https://api.helius.xyz/v0` |
| `DATABASE_URL` | Database connection string | `sqlite:///./app.db` |
| `MIN_CHILD_WALLETS` | Minimum children for detection | `5` |
| `DETECTION_WINDOW_MINUTES` | Detection time window | `5` |
| `ENVIRONMENT` | Application environment | `development` |
| `DEBUG` | Enable debug mode | `True` |

### Cluster Detection Parameters

- **Min Child Wallets**: Configurable minimum number of child wallets (3-20) required to classify as a cluster
- **Funding Window**: Time window in minutes (1-30) within which funding must occur to be considered coordinated
- **Detection Types**:
  - `BUY_CLUSTER`: Parent funds children with SOL for token purchases
  - `SELL_CLUSTER`: Parent distributes tokens to children for coordinated selling

## 📊 Features

### Current Implementation
- ✅ FastAPI application with async support
- ✅ Helius API integration for transaction data
- ✅ Wallet cluster detection algorithms
- ✅ SQLAlchemy database models
- ✅ Pydantic schemas for data validation
- ✅ Comprehensive API documentation
- ✅ Health monitoring endpoints
- ✅ Configurable detection parameters

### Dashboard Analytics Support
The backend is designed to support frontend dashboards with:
- **Parent Wallet Tracking**: Monitor funding patterns and distribution strategies
- **Token Activity Analysis**: Track buy/sell activities across child wallets
- **DEX Usage Patterns**: Identify preferred exchanges (Raydium, Meteora, Phoenix)
- **Timing Analysis**: Calculate buy intervals and completion estimates
- **Health Scoring**: Algorithmic scoring of cluster strength and coordination

## 🛠️ Development

### Development Setup

1. **Enable development mode**:
   ```bash
   export ENVIRONMENT=development
   export DEBUG=True
   ```

2. **Run with auto-reload**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **View logs**:
   The application includes structured logging for debugging and monitoring.

### Code Structure

- **Services**: Business logic separated into service classes
- **Models**: SQLAlchemy ORM models for data persistence
- **Schemas**: Pydantic models for request/response validation
- **APIs**: RESTful endpoints organized by functionality
- **Core**: Configuration, database, and security utilities

### Adding New Features

1. **Database Models**: Add new models in `app/models/`
2. **API Endpoints**: Create endpoints in `app/api/v1/endpoints/`
3. **Business Logic**: Implement services in `app/services/`
4. **Schemas**: Define request/response schemas in `app/schemas/`

## 🔒 Security

- **API Key Management**: Helius API keys configured via environment variables
- **Input Validation**: Pydantic schemas validate all API inputs
- **Error Handling**: Comprehensive error handling with appropriate HTTP status codes
- **Rate Limiting**: Consider implementing rate limiting for production use

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For questions and support:
- Check the [API Documentation](http://localhost:8000/docs) when running locally
- Review the test examples in `test_api.py`
- Examine the configuration options in `app/core/config.py`

---

**Built with FastAPI, SQLAlchemy, and Helius API for comprehensive Solana blockchain monitoring.** 
