# QuantumNest Mobile Frontend

A Next.js-based Progressive Web App (PWA) for the QuantumNest investment platform.

## Overview

This is the mobile-optimized web frontend for QuantumNest, built with:

- **Next.js 15** with App Router
- **TypeScript** for type safety
- **TailwindCSS** for styling
- **Radix UI** components
- **Chart.js** for data visualization
- **ethers.js** for blockchain integration

## Getting Started

### Prerequisites

- Node.js 14+ or pnpm
- Backend API running (see backend setup below)

### Installation

```bash
# Install dependencies
npm install --legacy-peer-deps
# or
pnpm install

# Copy environment variables
cp .env.example .env.local

# Update .env.local with your configuration
```

### Environment Variables

Create a `.env.local` file based on `.env.example`:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Blockchain Configuration
NEXT_PUBLIC_BLOCKCHAIN_NETWORK=goerli
NEXT_PUBLIC_INFURA_PROJECT_ID=your_infura_project_id

# Feature Flags
NEXT_PUBLIC_ENABLE_BLOCKCHAIN=false
NEXT_PUBLIC_ENABLE_AI_RECOMMENDATIONS=true
```

### Development

```bash
# Run development server
npm run dev
# or
pnpm dev

# Open http://localhost:3000 in your browser
```

### Building

```bash
# Build for production
npm run build
# or
pnpm build

# Start production server
npm start
# or
pnpm start
```

### Testing

```bash
# Run tests
npm test
# or
pnpm test

# Run tests with coverage
npm test -- --coverage
```

## Project Structure

```
mobile-frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── dashboard/         # Dashboard page
│   │   ├── portfolio/         # Portfolio management
│   │   ├── market-analysis/   # Market analysis
│   │   ├── recommendations/   # AI recommendations
│   │   └── __tests__/         # Page tests
│   ├── components/
│   │   ├── layout/            # Layout components (Navbar, BottomNav)
│   │   ├── ui/                # Reusable UI components
│   │   ├── portfolio/         # Portfolio-specific components
│   │   └── __tests__/         # Component tests
│   ├── lib/
│   │   ├── api.tsx            # API client and context
│   │   ├── blockchain.tsx     # Blockchain integration
│   │   ├── utils.ts           # Utility functions
│   │   └── __tests__/         # Library tests
│   └── hooks/                 # Custom React hooks
├── public/                    # Static assets
│   ├── manifest.json          # PWA manifest
│   └── icons/                 # App icons
├── .env.example               # Environment variables template
├── jest.config.js             # Jest configuration
├── jest.setup.js              # Jest setup file
├── next.config.ts             # Next.js configuration
├── tailwind.config.ts         # Tailwind configuration
└── tsconfig.json              # TypeScript configuration
```

## Features

### Implemented

✅ **Dashboard**

- Portfolio overview with stats
- Performance charts
- Recent transactions
- AI insights

✅ **Portfolio Management**

- Multiple portfolios support
- Asset allocation visualization
- Performance analytics with Sharpe ratio, volatility, drawdown
- Complete transaction history with filtering

✅ **Market Analysis**

- Real-time market stats
- Trending assets
- Sector performance
- Market news

✅ **AI Recommendations**

- Personalized investment suggestions
- Risk-based recommendations
- Market sentiment analysis
- Portfolio optimization tips

✅ **Mobile Optimization**

- Responsive design for all screen sizes
- Touch-friendly interactions
- Bottom navigation for mobile
- Optimized tables and charts

✅ **PWA Features**

- Installable on mobile devices
- Offline-ready manifest
- Mobile-first design

### Testing Coverage

- Unit tests for all major components
- Integration tests for page flows
- API client tests
- Utility function tests

## Backend Integration

### Setting Up the Backend

1. Navigate to the backend directory:

```bash
cd ../code/backend
```

2. Set up Python environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure backend environment variables (create `.env` in backend):

```env
DATABASE_URL=postgresql://user:password@localhost/quantumnest
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
```

4. Run database migrations:

```bash
python manage.py migrate
```

5. Start the backend server:

```bash
python manage.py runserver
# or
uvicorn main:app --reload
```

The backend should now be running on `http://localhost:8000`.

### API Endpoints Used

The mobile frontend communicates with these backend endpoints:

- `GET /api/portfolio/stats` - Portfolio statistics
- `GET /api/portfolio/list` - User portfolios
- `GET /api/assets/trending` - Trending assets
- `GET /api/market/stats` - Market statistics
- `GET /api/recommendations` - AI recommendations
- `POST /api/transactions` - Create transaction
- `GET /api/transactions/history` - Transaction history

## Blockchain Integration

### Setup (Optional)

1. Install MetaMask or another Ethereum wallet
2. Add Goerli testnet to your wallet
3. Get testnet ETH from a faucet
4. Update `.env.local` with your Infura project ID
5. Set `NEXT_PUBLIC_ENABLE_BLOCKCHAIN=true`

### Features

- Wallet connection (MetaMask)
- Smart contract interactions
- Tokenized asset management
- On-chain portfolio tracking

## Troubleshooting

### Common Issues

**Build errors with peer dependencies:**

```bash
npm install --legacy-peer-deps
```

**Port 3000 already in use:**

```bash
# Use a different port
PORT=3001 npm run dev
```

**API connection errors:**

- Ensure backend is running on `http://localhost:8000`
- Check `.env.local` has correct `NEXT_PUBLIC_API_URL`
- Verify CORS is configured on backend

## Performance Optimization

- Dynamic imports for heavy components
- Image optimization with Next.js Image
- Code splitting with App Router
- Chart.js lazy loading
- Responsive images and icons

## Contributing

1. Fix import case sensitivity issues
2. Follow existing code structure
3. Add tests for new features
4. Update documentation

## License

MIT License - see LICENSE file for details
