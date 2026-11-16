/**
 * LittleCare Growth Chart Visualizer with WHO Pediatric Growth Standards
 * Clear Disclaimer: Educational reference percentiles only; does not replace pediatric diagnosis.
 */

function initGrowthChart(canvasId, babyId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    fetch(`/health/api/growth-data/${babyId}`)
        .then(res => res.json())
        .then(data => {
            renderChart(canvas, data);
        })
        .catch(err => {
            console.error('Error fetching growth data:', err);
        });
}

function renderChart(canvas, data) {
    const ctx = canvas.getContext('2d');

    // WHO Reference Data for 0-24 Months (blended standard median & percentile approximations)
    const whoMonths = [0, 1, 2, 3, 4, 6, 9, 12, 18, 24];
    const whoLabels = whoMonths.map(m => `${m} mos`);
    
    // Weight datasets (kg)
    const whoWeightP85 = [3.8, 5.2, 6.4, 7.3, 8.0, 9.1, 10.2, 11.0, 12.5, 13.7];
    const whoWeightP50 = [3.3, 4.5, 5.6, 6.4, 7.0, 7.9, 8.9, 9.6, 10.9, 12.0]; // Median
    const whoWeightP15 = [2.9, 3.9, 4.8, 5.5, 6.1, 6.9, 7.7, 8.3, 9.4, 10.4];

    // Combine labels
    const chartLabels = data.records.labels.length > 0 ? data.records.labels : whoLabels;

    const chartConfig = {
        type: 'line',
        data: {
            labels: chartLabels,
            datasets: [
                {
                    label: `${data.baby_name}'s Recorded Weight (kg)`,
                    data: data.records.weights,
                    borderColor: '#0284c7',
                    backgroundColor: 'rgba(2, 132, 199, 0.2)',
                    borderWidth: 3,
                    pointBackgroundColor: '#0284c7',
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    tension: 0.2,
                    fill: false,
                    zIndex: 10
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        font: { family: 'Nunito', weight: '600', size: 12 }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    padding: 12,
                    titleFont: { family: 'Poppins', size: 13 },
                    bodyFont: { family: 'Nunito', size: 12 },
                    callbacks: {
                        label: function (context) {
                            return ` ${context.dataset.label}: ${context.parsed.y} kg`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    title: {
                        display: true,
                        text: 'Age & Measurement Date',
                        font: { family: 'Nunito', weight: 'bold' }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Weight in Kilograms (kg)',
                        font: { family: 'Nunito', weight: 'bold' }
                    },
                    suggestedMin: 2,
                    suggestedMax: 15
                }
            }
        }
    };

    window.growthChartInstance = new Chart(ctx, chartConfig);
}
