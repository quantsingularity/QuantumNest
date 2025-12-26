import { formatCurrency, formatPercentage } from '../utils';

describe('Utils', () => {
    describe('formatCurrency', () => {
        it('formats positive numbers correctly', () => {
            expect(formatCurrency(1000)).toBe('$1,000.00');
            expect(formatCurrency(1500.5)).toBe('$1,500.50');
        });

        it('formats large numbers correctly', () => {
            expect(formatCurrency(1000000)).toBe('$1,000,000.00');
        });

        it('formats zero correctly', () => {
            expect(formatCurrency(0)).toBe('$0.00');
        });
    });

    describe('formatPercentage', () => {
        it('formats positive percentages correctly', () => {
            expect(formatPercentage(5.5)).toBe('+5.50%');
            expect(formatPercentage(10)).toBe('+10.00%');
        });

        it('formats negative percentages correctly', () => {
            expect(formatPercentage(-3.2)).toBe('-3.20%');
        });

        it('formats zero correctly', () => {
            expect(formatPercentage(0)).toBe('0.00%');
        });
    });
});
