document.addEventListener('DOMContentLoaded', () => {
    const PARAM_NAMES = ['delta', 'nelectron', 'bmag', 'asize'];
    const EXAMPLE_SETTINGS_PATHS = [
        '../../examples/parameter_study_settings.json',
        '/examples/parameter_study_settings.json',
        'examples/parameter_study_settings.json'
    ];
    const API_BASE_URL = window.APP_CONFIG?.API_BASE_URL || 'http://localhost:8000';

    const form = document.getElementById('gsyncForm');
    const runBtn = document.getElementById('runBtn');
    const loader = document.getElementById('loader');
    const resultsPanel = document.getElementById('resultsPanel');
    const resultImage = document.getElementById('resultImage');
    const resultChartCanvas = document.getElementById('resultChart');
    let spectrumChart = null;
    
    // JSON Import/Export Elements
    const importJsonBtn = document.getElementById('importJsonBtn');
    const exportJsonBtn = document.getElementById('exportJsonBtn');
    const fillExampleBtn = document.getElementById('fillExampleBtn');
    const jsonFile = document.getElementById('jsonFile');

    // Visibility Logic for Parameter Inputs
    const studyParams = document.querySelectorAll('input[name="study_param"]');

    function parseNumber(value) {
        const parsed = parseFloat(value);
        return Number.isNaN(parsed) ? null : parsed;
    }

    function getSelectedParam() {
        return document.querySelector('input[name="study_param"]:checked').value;
    }

    function getExportData() {
        return {
            viewAngle: parseNumber(document.getElementById('viewAngle').value),
            height: parseNumber(document.getElementById('height').value),
            j1: parseInt(document.getElementById('j1').value, 10),
            j2: parseInt(document.getElementById('j2').value, 10),
            etr: parseNumber(document.getElementById('etr').value),
            np: parseNumber(document.getElementById('np').value),
            study_param: getSelectedParam(),
            delta: getParamValues('delta'),
            nelectron: getParamValues('nelectron'),
            bmag: getParamValues('bmag'),
            asize: getParamValues('asize')
        };
    }

    function applySettings(data) {
        if (data.viewAngle !== undefined) document.getElementById('viewAngle').value = data.viewAngle;
        if (data.height !== undefined) document.getElementById('height').value = data.height;
        if (data.j1 !== undefined) document.getElementById('j1').value = data.j1;
        if (data.j2 !== undefined) document.getElementById('j2').value = data.j2;
        if (data.etr !== undefined) document.getElementById('etr').value = data.etr;
        if (data.np !== undefined) document.getElementById('np').value = data.np;

        const selectedParam = data.study_param || getSelectedParam();
        const selectedRadio = document.querySelector(`input[name="study_param"][value="${selectedParam}"]`);
        if (selectedRadio) {
            selectedRadio.checked = true;
        }

        PARAM_NAMES.forEach(paramName => {
            const rawValue = data[paramName] ?? data.params?.[paramName]?.value;
            const values = Array.isArray(rawValue) ? rawValue : rawValue !== undefined ? [rawValue] : [];

            for (let index = 1; index <= 4; index += 1) {
                const input = document.getElementById(`${paramName}_val_${index}`);
                input.value = values[index - 1] ?? '';
            }
        });

        updateInputVisibility();
    }

    function downloadJsonFile(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(url);
    }

    async function loadExampleSettings() {
        for (const path of EXAMPLE_SETTINGS_PATHS) {
            try {
                const response = await fetch(path);
                if (response.ok) {
                    return await response.json();
                }
            } catch (error) {
                console.error(`Failed to load example from ${path}`, error);
            }
        }

        throw new Error('Could not locate parameter_study_settings.json');
    }
    
    function updateInputVisibility() {
        const selectedValue = getSelectedParam();
        
        ['delta', 'nelectron', 'bmag', 'asize'].forEach(param => {
            const row = document.getElementById(`${param}_row`);
            if (!row) return; // safety check
            
            // Get inputs 2, 3, 4
            const inputs = [
                document.getElementById(`${param}_val_2`),
                document.getElementById(`${param}_val_3`),
                document.getElementById(`${param}_val_4`)
            ];
            
            if (param === selectedValue) {
                // Show extra inputs
                inputs.forEach(input => input.classList.remove('hidden'));
            } else {
                // Hide extra inputs and clear their values
                inputs.forEach(input => {
                    input.classList.add('hidden');
                    input.value = ''; 
                });
            }
        });
    }

    // Initialize visibility on load
    updateInputVisibility();

    // Add event listeners to radio buttons
    studyParams.forEach(radio => {
        radio.addEventListener('change', updateInputVisibility);
    });

    // JSON Export Logic
    exportJsonBtn.addEventListener('click', () => {
        downloadJsonFile(getExportData(), 'parameter_study_settings.json');
    });

    // JSON Import Logic
    importJsonBtn.addEventListener('click', () => jsonFile.click());

    fillExampleBtn.addEventListener('click', async () => {
        try {
            const exampleData = await loadExampleSettings();
            applySettings(exampleData);
        } catch (error) {
            console.error(error);
            alert(`Unable to load example settings: ${error.message}`);
        }
    });

    jsonFile.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const data = JSON.parse(event.target.result);
                applySettings(data);
                e.target.value = ''; // Reset
                
            } catch (err) {
                alert('Error parsing JSON file: ' + err.message);
            }
        };
        reader.readAsText(file);
    });

    function getParamValues(paramName) {
        // Collect values from inputs named paramName_val_1 to _4
        const selectedParam = getSelectedParam();
        
        let values = [];
        // Always get the first value
        const el1 = document.getElementById(`${paramName}_val_1`);
        if (el1 && el1.value !== "") {
            const val = parseFloat(el1.value);
            if (!isNaN(val)) values.push(val);
        }

        if (selectedParam === paramName) {
            // Collect up to 3 more values
            for (let i = 2; i <= 4; i++) {
                const el = document.getElementById(`${paramName}_val_${i}`);
                if (el && el.value !== "" && !el.classList.contains('hidden')) {
                    const val = parseFloat(el.value);
                    if (!isNaN(val)) {
                        values.push(val);
                    }
                }
            }
        }
        
        return values;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        loader.classList.remove('hidden');
        resultsPanel.classList.add('hidden');
        runBtn.disabled = true;

        try {
            // Construct payload matching ParameterImpactRequest
            const formData = {
                viewAngle: parseNumber(document.getElementById('viewAngle').value),
                height: parseNumber(document.getElementById('height').value),
                j1: parseInt(document.getElementById('j1').value, 10),
                j2: parseInt(document.getElementById('j2').value, 10),
                etr: parseNumber(document.getElementById('etr').value),
                np: parseNumber(document.getElementById('np').value),
                delta: getParamValues('delta'),
                nelectron: getParamValues('nelectron'),
                bmag: getParamValues('bmag'),
                asize: getParamValues('asize')
            };

            const apiUrl = `${API_BASE_URL}/parameterImpact`;

            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Simulation Failed');
            }

            const result = await response.json();
            displayResults(result.data);

        } catch (error) {
            console.error(error);
            alert('Simulation Aborted: ' + error.message);
        } finally {
            loader.classList.add('hidden');
            runBtn.disabled = false;
        }
    });

    function displayResults(data) {
        resultsPanel.classList.remove('hidden');
        
        if (data.image) {
            resultImage.src = `data:image/png;base64,${data.image}`;
        }

        renderSpectrumChart(data.bins, data.flux_results);
        
        resultsPanel.scrollIntoView({ behavior: 'smooth' });
    }

    function renderSpectrumChart(bins, fluxResults) {
        if (typeof Chart === 'undefined') {
            return;
        }

        if (spectrumChart) {
            spectrumChart.destroy();
            spectrumChart = null;
        }

        if (!Array.isArray(bins) || bins.length === 0 || !Array.isArray(fluxResults) || fluxResults.length === 0) {
            return;
        }

        const palette = ['#00d2ff', '#ff4d4d', '#9d50bb', '#00f5a0', '#ffd166', '#ef476f'];
        const datasets = fluxResults
            .map((series, index) => {
                const parameterValue = series.parameterValue ?? series.parameter_value ?? series.parameter;
                const label = `${series.prefix} - ${parameterValue}`;
                const points = bins
                    .map((x, pointIndex) => ({
                        x: Number(x),
                        y: Number(series.flux?.[pointIndex])
                    }))
                    .filter(point => point.x > 0 && point.y > 0);

                if (points.length === 0) {
                    return null;
                }

                const color = palette[index % palette.length];
                return {
                    label,
                    data: points,
                    borderColor: color,
                    backgroundColor: `${color}33`,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    borderWidth: 2,
                    tension: 0,
                    fill: false
                };
            })
            .filter(Boolean);

        if (datasets.length === 0) {
            return;
        }

        spectrumChart = new Chart(resultChartCanvas, {
            type: 'line',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'nearest',
                    intersect: false
                },
                plugins: {
                    title: {
                        display: false
                    },
                    legend: {
                        labels: {
                            color: '#e0e0e0'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            title() {
                                return '';
                            },
                            label(context) {
                                const xValue = Number(context.parsed.x);
                                const yValue = Number(context.parsed.y);
                                return [
                                    `Series: ${context.dataset.label}`,
                                    `Frequency (Hz): ${xValue.toExponential(4)}`,
                                    `Flux Density (SFU): ${yValue.toExponential(4)}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'logarithmic',
                        title: {
                            display: true,
                            text: 'Frequency (Hz)',
                            color: '#00d2ff'
                        },
                        ticks: {
                            color: '#e0e0e0',
                            callback(value) {
                                const numericValue = Number(value);
                                const exponent = Math.log10(numericValue);
                                return Number.isInteger(exponent) ? numericValue.toExponential(0) : '';
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.08)'
                        }
                    },
                    y: {
                        type: 'logarithmic',
                        title: {
                            display: true,
                            text: 'Flux Density (SFU)',
                            color: '#00d2ff'
                        },
                        ticks: {
                            color: '#e0e0e0',
                            callback(value) {
                                return Number(value).toExponential(2);
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.08)'
                        }
                    }
                }
            }
        });
    }
});
