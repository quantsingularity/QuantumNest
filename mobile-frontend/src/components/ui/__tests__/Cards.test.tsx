import React from 'react';
import { render, screen } from '@testing-library/react';
import { StatCard, AssetCard, PortfolioCard } from '../Cards';

describe('StatCard', () => {
    it('renders title and value', () => {
        render(<StatCard title="Test Stat" value="$1,000" />);
        expect(screen.getByText('Test Stat')).toBeInTheDocument();
        expect(screen.getByText('$1,000')).toBeInTheDocument();
    });

    it('renders positive change indicator', () => {
        render(<StatCard title="Portfolio" value="$1,000" change={5.5} />);
        expect(screen.getByText('↑')).toBeInTheDocument();
        expect(screen.getByText('5.50%')).toBeInTheDocument();
    });

    it('renders negative change indicator', () => {
        render(<StatCard title="Portfolio" value="$1,000" change={-3.2} />);
        expect(screen.getByText('↓')).toBeInTheDocument();
        expect(screen.getByText('3.20%')).toBeInTheDocument();
    });
});

describe('AssetCard', () => {
    it('renders asset information', () => {
        render(<AssetCard symbol="BTC" name="Bitcoin" price={65000} change24h={2.5} />);
        expect(screen.getByText('Bitcoin')).toBeInTheDocument();
        expect(screen.getByText('BTC')).toBeInTheDocument();
    });

    it('renders market cap when provided', () => {
        render(
            <AssetCard
                symbol="BTC"
                name="Bitcoin"
                price={65000}
                change24h={2.5}
                marketCap={1280000000000}
            />,
        );
        expect(screen.getByText('Market Cap')).toBeInTheDocument();
    });
});

describe('PortfolioCard', () => {
    it('renders portfolio information', () => {
        render(
            <PortfolioCard name="Growth Portfolio" value={750000} change={8.5} assetCount={8} />,
        );
        expect(screen.getByText('Growth Portfolio')).toBeInTheDocument();
        expect(screen.getByText('8 assets')).toBeInTheDocument();
    });

    it('renders last updated date when provided', () => {
        render(
            <PortfolioCard
                name="Growth Portfolio"
                value={750000}
                assetCount={8}
                lastUpdated="2025-04-12"
            />,
        );
        expect(screen.getByText(/Updated: 2025-04-12/)).toBeInTheDocument();
    });
});
