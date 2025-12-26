// Portfolio Performance Tab Component
'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { LineChart } from '@/components/ui/Charts';
import { StatCard } from '@/components/ui/Cards';

export default function PerformanceTab() {
    // Mock performance data
    const performanceStats = [
        { title: 'Total Return', value: '+$125,000', change: 12.5 },
        { title: 'YTD Return', value: '+8.3%', change: 8.3 },
        { title: 'Best Performer', value: 'NVDA', change: 45.2 },
        { title: 'Worst Performer', value: 'TSLA', change: -4.2 },
    ];

    // Performance chart data
    const performanceData = {
        labels: [
            'Jan',
            'Feb',
            'Mar',
            'Apr',
            'May',
            'Jun',
            'Jul',
            'Aug',
            'Sep',
            'Oct',
            'Nov',
            'Dec',
        ],
        datasets: [
            {
                label: 'Portfolio Value',
                data: [
                    1000000, 1025000, 1050000, 1075000, 1100000, 1125000, 1150000, 1175000, 1200000,
                    1225000, 1240000, 1250000,
                ],
                borderColor: 'rgba(99, 102, 241, 1)',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                fill: true,
            },
            {
                label: 'Benchmark (S&P 500)',
                data: [
                    1000000, 1015000, 1030000, 1045000, 1055000, 1070000, 1085000, 1095000, 1110000,
                    1120000, 1130000, 1140000,
                ],
                borderColor: 'rgba(156, 163, 175, 1)',
                backgroundColor: 'rgba(156, 163, 175, 0.1)',
                fill: true,
            },
        ],
    };

    // Monthly returns data
    const monthlyReturns = [
        { month: 'January', return: 2.5, benchmark: 1.5 },
        { month: 'February', return: 2.4, benchmark: 1.5 },
        { month: 'March', return: 2.4, benchmark: 1.5 },
        { month: 'April', return: 2.4, benchmark: 1.5 },
        { month: 'May', return: 2.3, benchmark: 1.0 },
        { month: 'June', return: 2.3, benchmark: 1.4 },
        { month: 'July', return: 2.2, benchmark: 1.4 },
        { month: 'August', return: 2.2, benchmark: 1.0 },
        { month: 'September', return: 2.1, benchmark: 1.4 },
        { month: 'October', return: 2.1, benchmark: 0.9 },
        { month: 'November', return: 1.2, benchmark: 0.9 },
        { month: 'December', return: 0.8, benchmark: 0.9 },
    ];

    return (
        <div className="space-y-6">
            {/* Performance Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-4">
                {performanceStats.map((stat, index) => (
                    <StatCard
                        key={index}
                        title={stat.title}
                        value={stat.value}
                        change={stat.change}
                    />
                ))}
            </div>

            {/* Performance Chart */}
            <div>
                <LineChart
                    data={performanceData}
                    title="Portfolio Performance vs Benchmark"
                    height={300}
                />
            </div>

            {/* Monthly Returns */}
            <Card>
                <CardHeader>
                    <CardTitle>Monthly Returns</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs uppercase bg-gray-50 dark:bg-gray-800">
                                <tr>
                                    <th className="px-4 py-3">Month</th>
                                    <th className="px-4 py-3 text-right">Portfolio</th>
                                    <th className="px-4 py-3 text-right">Benchmark</th>
                                    <th className="px-4 py-3 text-right">Difference</th>
                                </tr>
                            </thead>
                            <tbody>
                                {monthlyReturns.map((data, index) => {
                                    const diff = data.return - data.benchmark;
                                    return (
                                        <tr
                                            key={index}
                                            className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
                                        >
                                            <td className="px-4 py-3 font-medium">{data.month}</td>
                                            <td className="px-4 py-3 text-right text-green-600 dark:text-green-400">
                                                +{data.return.toFixed(1)}%
                                            </td>
                                            <td className="px-4 py-3 text-right">
                                                +{data.benchmark.toFixed(1)}%
                                            </td>
                                            <td
                                                className={`px-4 py-3 text-right font-medium ${
                                                    diff > 0
                                                        ? 'text-green-600 dark:text-green-400'
                                                        : 'text-red-600 dark:text-red-400'
                                                }`}
                                            >
                                                {diff > 0 ? '+' : ''}
                                                {diff.toFixed(1)}%
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            {/* Risk Metrics */}
            <Card>
                <CardHeader>
                    <CardTitle>Risk Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div>
                            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                                Sharpe Ratio
                            </p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">1.85</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                Above average risk-adjusted returns
                            </p>
                        </div>
                        <div>
                            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                                Volatility
                            </p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                14.2%
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                Moderate risk level
                            </p>
                        </div>
                        <div>
                            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                                Max Drawdown
                            </p>
                            <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                                -8.5%
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                Largest peak-to-trough decline
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
