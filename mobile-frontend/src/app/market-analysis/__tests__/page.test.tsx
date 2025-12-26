import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import MarketAnalysis from '../page';

describe('Market Analysis Page', () => {
    it('renders market analysis title', () => {
        render(<MarketAnalysis />);
        expect(screen.getByText('Market Analysis')).toBeInTheDocument();
    });

    it('renders all tabs', () => {
        render(<MarketAnalysis />);
        expect(screen.getByText('Overview')).toBeInTheDocument();
        expect(screen.getByText('Stocks')).toBeInTheDocument();
        expect(screen.getByText('Crypto')).toBeInTheDocument();
        expect(screen.getByText('News')).toBeInTheDocument();
    });

    it('displays market stats', () => {
        render(<MarketAnalysis />);
        expect(screen.getByText('S&P 500')).toBeInTheDocument();
        expect(screen.getByText('NASDAQ')).toBeInTheDocument();
        expect(screen.getByText('Bitcoin')).toBeInTheDocument();
    });

    it('switches to news tab when clicked', () => {
        render(<MarketAnalysis />);
        const newsTab = screen.getByText('News');
        fireEvent.click(newsTab);
        expect(screen.getByText('Latest Market News')).toBeInTheDocument();
    });

    it('renders time range buttons', () => {
        render(<MarketAnalysis />);
        expect(screen.getByText('1W')).toBeInTheDocument();
        expect(screen.getByText('1M')).toBeInTheDocument();
        expect(screen.getByText('3M')).toBeInTheDocument();
        expect(screen.getByText('1Y')).toBeInTheDocument();
    });
});
