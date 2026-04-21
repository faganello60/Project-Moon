document.addEventListener('DOMContentLoaded', () => {
    const PARAM_NAMES = ['delta', 'nelectron', 'bmag', 'asize'];
    const EXAMPLE_SETTINGS_PATH = '../examples/demo_settings.json';
    const API_BASE_URL = window.APP_CONFIG?.API_BASE_URL || 'http://localhost:8000';

    const form = document.getElementById('gsyncForm');
    const runBtn = document.getElementById('runBtn');
    const runBtnPython = document.getElementById('runBtnPython');
    const loader = document.getElementById('loader');
    const resultsPanel = document.getElementById('resultsPanel');
    const resultImage = document.getElementById('resultImage');
    const resultChartCanvas = document.getElementById('resultChart');
    const resultViewButtons = document.querySelectorAll('.view-toggle-btn');
    const resultViewPanels = document.querySelectorAll('[data-result-view]');
    const fitReport = document.getElementById('fitReport');
    const bestValuesContainer = document.getElementById('bestValues');
    const datFile = document.getElementById('datFile');
    const xDataText = document.getElementById('xData');
    const yDataText = document.getElementById('yData');
    const importMode = document.getElementById('importMode');
    const importContainer = document.getElementById('importContainer');
    const importJsonBtn = document.getElementById('importJsonBtn');
    const exportJsonBtn = document.getElementById('exportJsonBtn');
    const fillExampleBtn = document.getElementById('fillExampleBtn');
    const jsonFile = document.getElementById('jsonFile');
    const exportResultsBtn = document.getElementById('exportResultsBtn');

    let currentEndpoint = '/gsync';
    let lastSimulationData = null;
    let lastRequestData = null;
    let spectrumChart = null;
    let activeResultView = 'chart';

    function parseNumber(value) {
        const parsed = parseFloat(value);
        return Number.isNaN(parsed) ? null : parsed;
    }

    function formatScientificInput(value) {
        const numericValue = Number(value);
        if (!Number.isFinite(numericValue) || numericValue === 0) return value;

        return numericValue.toExponential();
    }

    function stringifySettingsJson(data) {
        return JSON.stringify(data, (key, value) => {
            if ((key === 'height' || key === 'np') && Number.isFinite(value) && value !== 0) {
                return `__SCIENTIFIC_NUMBER__${value.toExponential()}__`;
            }

            return value;
        }, 2).replace(/"__SCIENTIFIC_NUMBER__([^"]+)__"/g, '$1');
    }

    function toSuperscript(value) {
        const superscriptDigits = {
            '-': '\u207B',
            0: '\u2070',
            1: '\u00B9',
            2: '\u00B2',
            3: '\u00B3',
            4: '\u2074',
            5: '\u2075',
            6: '\u2076',
            7: '\u2077',
            8: '\u2078',
            9: '\u2079'
        };

        return String(value).split('').map(char => superscriptDigits[char] ?? char).join('');
    }

    function formatLogPowerTick(value) {
        const numericValue = Number(value);
        if (numericValue <= 0) return '';

        const exponent = Math.log10(numericValue);
        const roundedExponent = Math.round(exponent);
        if (Math.abs(exponent - roundedExponent) > 1e-8) return '';

        return `10${toSuperscript(roundedExponent)}`;
    }

    function updateResultView(view) {
        activeResultView = view;

        resultViewButtons.forEach(button => {
            button.classList.toggle('active', button.dataset.view === view);
        });

        resultViewPanels.forEach(panel => {
            panel.classList.toggle('hidden', panel.dataset.resultView !== view);
        });

        if (view === 'chart' && spectrumChart) {
            spectrumChart.resize();
        }
    }

    function getParamConfig(name) {
        const vary = document.getElementById(`${name}_vary`).checked;
        const value = parseNumber(document.getElementById(`${name}_val`).value);

        if (!vary) {
            return {
                value,
                min: 0,
                max: 0,
                vary: false
            };
        }

        return {
            value,
            min: parseNumber(document.getElementById(`${name}_min`).value),
            max: parseNumber(document.getElementById(`${name}_max`).value),
            vary: true
        };
    }

    function buildFormData() {
        return {
            prefix: document.getElementById('prefix').value,
            viewAngle: parseNumber(document.getElementById('viewAngle').value),
            height: parseNumber(document.getElementById('height').value),
            emin: parseNumber(document.getElementById('emin').value),
            emax: parseNumber(document.getElementById('emax').value),
            etr: parseNumber(document.getElementById('etr').value),
            np: parseNumber(document.getElementById('np').value),
            freq: document.getElementById('xData').value.split(',').map(v => parseFloat(v.trim())).filter(v => !Number.isNaN(v)),
            sfu: document.getElementById('yData').value.split(',').map(v => parseFloat(v.trim())).filter(v => !Number.isNaN(v)),
            params: PARAM_NAMES.reduce((acc, name) => {
                acc[name] = getParamConfig(name);
                return acc;
            }, {})
        };
    }

    function updateParamRowState(name) {
        const row = document.querySelector(`.param-row[data-param="${name}"]`);
        const varyCheckbox = document.getElementById(`${name}_vary`);
        const valueLabel = row.querySelector(`label[for="${name}_val"]`);
        const minInput = document.getElementById(`${name}_min`);
        const maxInput = document.getElementById(`${name}_max`);
        const isFixed = !varyCheckbox.checked;

        row.classList.toggle('is-fixed', isFixed);
        valueLabel.textContent = isFixed ? 'Value' : 'Initial Guess';
        minInput.disabled = isFixed;
        maxInput.disabled = isFixed;

        if (isFixed) {
            minInput.value = '';
            maxInput.value = '';
        }
    }

    function applySettings(data) {
        if (data.prefix !== undefined) document.getElementById('prefix').value = data.prefix;
        if (data.viewAngle !== undefined) document.getElementById('viewAngle').value = data.viewAngle;
        if (data.height !== undefined) document.getElementById('height').value = formatScientificInput(data.height);
        const importedEmin = data.emin ?? data.Emin;
        const importedEmax = data.emax ?? data.Emax;
        if (importedEmin !== undefined) document.getElementById('emin').value = importedEmin;
        if (importedEmax !== undefined) document.getElementById('emax').value = importedEmax;
        if (data.etr !== undefined) document.getElementById('etr').value = data.etr;
        if (data.np !== undefined) document.getElementById('np').value = formatScientificInput(data.np);

        if (Array.isArray(data.freq)) document.getElementById('xData').value = data.freq.join(', ');
        if (Array.isArray(data.sfu)) document.getElementById('yData').value = data.sfu.join(', ');

        if (data.params) {
            PARAM_NAMES.forEach(name => {
                const param = data.params[name];
                if (!param) return;

                document.getElementById(`${name}_val`).value = param.value ?? '';
                document.getElementById(`${name}_vary`).checked = Boolean(param.vary);
                document.getElementById(`${name}_min`).value = param.min ?? '';
                document.getElementById(`${name}_max`).value = param.max ?? '';
                updateParamRowState(name);
            });
        }
    }

    function downloadJsonFile(data, filename) {
        const blob = new Blob([stringifySettingsJson(data)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(url);
    }

    async function loadExampleSettings() {
        const response = await fetch(EXAMPLE_SETTINGS_PATH);
        if (!response.ok) {
            throw new Error(`Could not load ${EXAMPLE_SETTINGS_PATH}`);
        }
        return response.json();
    }

    exportResultsBtn.addEventListener('click', () => {
        if (!lastSimulationData) return;

        const zip = new JSZip();
        const prefix = document.getElementById('prefix').value || 'Unknown';
        const imgData = lastSimulationData.image.replace(/^data:image\/(png|jpg);base64,/, '');
        zip.file(`SOL${prefix}.png`, imgData, { base64: true });

        if (lastSimulationData.bins && lastSimulationData.flux) {
            let datContent = '';
            for (let i = 0; i < lastSimulationData.bins.length; i += 1) {
                datContent += `${lastSimulationData.bins[i]} ${lastSimulationData.flux[i]}\n`;
            }
            zip.file(`fluxSOL${prefix}.dat`, datContent);
        }

        zip.generateAsync({ type: 'blob' }).then(content => {
            const url = URL.createObjectURL(content);
            const link = document.createElement('a');
            link.href = url;
            link.download = `SOL${prefix}_Results.zip`;
            link.click();
            URL.revokeObjectURL(url);
        });
    });

    exportJsonBtn.addEventListener('click', () => {
        const formData = buildFormData();
        downloadJsonFile(formData, `gsync_settings_${formData.prefix || 'config'}.json`);
    });

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

    jsonFile.addEventListener('change', e => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = event => {
            try {
                const data = JSON.parse(event.target.result);
                applySettings(data);
                e.target.value = '';
            } catch (error) {
                alert(`Error parsing JSON file: ${error.message}`);
            }
        };
        reader.readAsText(file);
    });

    runBtn.addEventListener('click', () => {
        currentEndpoint = '/gsync';
    });

    runBtnPython.addEventListener('click', () => {
        currentEndpoint = '/python/gsync';
    });

    resultViewButtons.forEach(button => {
        button.addEventListener('click', () => updateResultView(button.dataset.view));
    });

    importMode.addEventListener('change', () => {
        if (importMode.checked) {
            importContainer.classList.remove('hidden');
            xDataText.placeholder = 'Importing from file...';
            yDataText.placeholder = 'Importing from file...';
            xDataText.readOnly = true;
            yDataText.readOnly = true;
            xDataText.style.opacity = '0.7';
            yDataText.style.opacity = '0.7';
            return;
        }

        importContainer.classList.add('hidden');
        xDataText.placeholder = 'e.g. 1e9, 2e9, 5e9';
        yDataText.placeholder = 'e.g. 10, 50, 150';
        xDataText.readOnly = false;
        yDataText.readOnly = false;
        xDataText.style.opacity = '1';
        yDataText.style.opacity = '1';
    });

    datFile.addEventListener('change', e => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = event => {
            const content = event.target.result;
            const lines = content.trim().split('\n');
            const freqs = [];
            const fluxes = [];

            lines.forEach(line => {
                const parts = line.trim().split(/\s+/);
                if (parts.length >= 2) {
                    freqs.push(parts[0]);
                    fluxes.push(parts[1]);
                }
            });

            xDataText.value = freqs.join(', ');
            yDataText.value = fluxes.join(', ');

            const nameMatch = file.name.match(/NoRP (\d{4}-\d{2}-\d{2})/);
            if (nameMatch) {
                document.getElementById('prefix').value = nameMatch[1].replace(/-/g, '');
            }
        };
        reader.readAsText(file);
    });

    form.addEventListener('submit', async e => {
        e.preventDefault();

        loader.classList.remove('hidden');
        resultsPanel.classList.add('hidden');
        runBtn.disabled = true;
        runBtnPython.disabled = true;

        try {
            const formData = buildFormData();
            lastRequestData = formData;
            const apiUrl = `${API_BASE_URL}${currentEndpoint}`;
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
            alert(`Simulation Aborted: ${error.message}`);
        } finally {
            loader.classList.add('hidden');
            runBtn.disabled = false;
            runBtnPython.disabled = false;
        }
    });

    function displayResults(data) {
        lastSimulationData = data;
        resultsPanel.classList.remove('hidden');

        if (data.image) {
            resultImage.src = `data:image/png;base64,${data.image}`;
        }

        updateResultView(activeResultView);
        renderSpectrumChart(data.bins, data.flux, lastRequestData?.freq, lastRequestData?.sfu);

        fitReport.textContent = data.fit_report;
        bestValuesContainer.innerHTML = '';

        if (data.best_values) {
            Object.entries(data.best_values).forEach(([key, val]) => {
                const card = document.createElement('div');
                card.className = 'best-value-card';

                const label = document.createElement('span');
                label.className = 'best-value-label';
                label.textContent = key;

                const valueDisplay = document.createElement('span');
                valueDisplay.className = 'best-value-data';
                valueDisplay.textContent = typeof val === 'number' ? val.toExponential(4) : val;

                card.appendChild(label);
                card.appendChild(valueDisplay);
                bestValuesContainer.appendChild(card);
            });
        }

        resultsPanel.scrollIntoView({ behavior: 'smooth' });
    }

    function renderSpectrumChart(bins, flux, freq, sfu) {
        if (typeof Chart === 'undefined') {
            return;
        }

        if (spectrumChart) {
            spectrumChart.destroy();
            spectrumChart = null;
        }

        if (!Array.isArray(bins) || !Array.isArray(flux) || bins.length !== flux.length || bins.length === 0) {
            return;
        }

        const fitPoints = bins
            .map((x, index) => ({
                x: Number(x),
                y: Number(flux[index])
            }))
            .filter(point => point.x > 0 && point.y > 0);

        const observedPoints = Array.isArray(freq) && Array.isArray(sfu)
            ? freq
                .map((x, index) => ({
                    x: Number(x),
                    y: Number(sfu[index])
                }))
                .filter(point => point.x > 0 && point.y > 0)
            : [];

        if (fitPoints.length === 0) {
            return;
        }

        spectrumChart = new Chart(resultChartCanvas, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Fitting',
                    data: fitPoints,
                    borderColor: '#00d2ff',
                    backgroundColor: 'rgba(0, 210, 255, 0.18)',
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    borderWidth: 2,
                    tension: 0,
                    fill: false
                }, {
                    label: 'Observed Data',
                    data: observedPoints,
                    type: 'scatter',
                    showLine: false,
                    backgroundColor: '#ff4d4d',
                    borderColor: '#ffffff',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
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
                                return formatLogPowerTick(value);
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
                                return formatLogPowerTick(value);
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

    PARAM_NAMES.forEach(name => {
        document.getElementById(`${name}_vary`).addEventListener('change', () => {
            updateParamRowState(name);
        });
        updateParamRowState(name);
    });
});
