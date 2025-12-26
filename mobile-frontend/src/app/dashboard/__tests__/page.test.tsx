import React from 'react';
import { render, screen } from '@testing-library/react';
import Dashboard from '../page';

describe('Dashboard Page', () => {
    it('renders dashboard title', () => {
        render(<Dashboard />);
        expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    it('renders stat cards', () => {
        render(<Dashboard />);
        expect(screen.getByText('Portfolio Value')).toBeInTheDocument();
        expect(screen.getByText('Total Assets')).toBeInTheDocument();
    });

    it('renders AI Insights section', () => {
        render(<Dashboard />);
        expect(screen.getByText('AI Insights')).toBeInTheDocument();
        expect(screen.getByText('Portfolio Optimization')).toBeInTheDocument();
    });

    it('renders recent transactions table', () => {
        render(<Dashboard />);
        expect(screen.getByText('Recent Transactions')).toBeInTheDocument();
    });
});
