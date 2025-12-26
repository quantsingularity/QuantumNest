import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Portfolio from '../page';

describe('Portfolio Page', () => {
    it('renders portfolio management title', () => {
        render(<Portfolio />);
        expect(screen.getByText('Portfolio Management')).toBeInTheDocument();
    });

    it('renders all tabs', () => {
        render(<Portfolio />);
        expect(screen.getByText('My Portfolios')).toBeInTheDocument();
        expect(screen.getByText('Performance')).toBeInTheDocument();
        expect(screen.getByText('Transactions')).toBeInTheDocument();
    });

    it('switches to performance tab when clicked', () => {
        render(<Portfolio />);
        const performanceTab = screen.getByText('Performance');
        fireEvent.click(performanceTab);
        expect(screen.getByText('Total Return')).toBeInTheDocument();
    });

    it('switches to transactions tab when clicked', () => {
        render(<Portfolio />);
        const transactionsTab = screen.getByText('Transactions');
        fireEvent.click(transactionsTab);
        expect(screen.getByText('Transaction History')).toBeInTheDocument();
    });

    it('renders portfolio cards', () => {
        render(<Portfolio />);
        expect(screen.getByText('Growth Portfolio')).toBeInTheDocument();
        expect(screen.getByText('Income Portfolio')).toBeInTheDocument();
        expect(screen.getByText('Crypto Portfolio')).toBeInTheDocument();
    });
});
