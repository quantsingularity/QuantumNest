import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Recommendations from '../page';

describe('Recommendations Page', () => {
    it('renders AI recommendations title', () => {
        render(<Recommendations />);
        expect(screen.getByText('AI Recommendations')).toBeInTheDocument();
    });

    it('renders all tabs', () => {
        render(<Recommendations />);
        expect(screen.getByText('Personalized Recommendations')).toBeInTheDocument();
        expect(screen.getByText('Recommended Assets')).toBeInTheDocument();
        expect(screen.getByText('Market Insights')).toBeInTheDocument();
    });

    it('displays risk level selector', () => {
        render(<Recommendations />);
        expect(screen.getByText('Risk Level:')).toBeInTheDocument();
    });

    it('switches to recommended assets tab', () => {
        render(<Recommendations />);
        const assetsTab = screen.getByText('Recommended Assets');
        fireEvent.click(assetsTab);
        expect(screen.getByText('Top Recommended Assets')).toBeInTheDocument();
    });

    it('displays AI portfolio analysis', () => {
        render(<Recommendations />);
        expect(screen.getByText('AI Portfolio Analysis')).toBeInTheDocument();
    });
});
