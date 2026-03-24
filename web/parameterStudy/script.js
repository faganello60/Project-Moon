document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('gsyncForm');
    const runBtn = document.getElementById('runBtn');
    const loader = document.getElementById('loader');
    const resultsPanel = document.getElementById('resultsPanel');
    const resultImage = document.getElementById('resultImage');
    
    // JSON Import/Export Elements
    const importJsonBtn = document.getElementById('importJsonBtn');
    const exportJsonBtn = document.getElementById('exportJsonBtn');
    const jsonFile = document.getElementById('jsonFile');

    // Visibility Logic for Parameter Inputs
    const studyParams = document.querySelectorAll('input[name="study_param"]');
    
    function updateInputVisibility() {
        const selectedValue = document.querySelector('input[name="study_param"]:checked').value;
        
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
        const formData = {
            viewAngle: parseFloat(document.getElementById('viewAngle').value),
            height: parseFloat(document.getElementById('height').value),
            j1: parseInt(document.getElementById('j1').value),
            j2: parseInt(document.getElementById('j2').value),
            etr: parseFloat(document.getElementById('etr').value),
            np: parseFloat(document.getElementById('np').value),
            // We can export the "first" value of each parameter as a base, 
            // or the whole study setup. Let's export the first value for compatibility 
            // with the other tool, or just the values present.
            delta: parseFloat(document.getElementById('delta_val_1').value),
            nelectron: parseFloat(document.getElementById('nelectron_val_1').value),
            bmag: parseFloat(document.getElementById('bmag_val_1').value),
            asize: parseFloat(document.getElementById('asize_val_1').value)
        };

        const blob = new Blob([JSON.stringify(formData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `parameter_study_settings.json`;
        a.click();
        URL.revokeObjectURL(url);
    });

    // JSON Import Logic
    importJsonBtn.addEventListener('click', () => jsonFile.click());

    jsonFile.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const data = JSON.parse(event.target.result);
                
                if (data.viewAngle !== undefined) document.getElementById('viewAngle').value = data.viewAngle;
                if (data.height !== undefined) document.getElementById('height').value = data.height;
                if (data.j1 !== undefined) document.getElementById('j1').value = data.j1;
                if (data.j2 !== undefined) document.getElementById('j2').value = data.j2;
                if (data.etr !== undefined) document.getElementById('etr').value = data.etr;
                if (data.np !== undefined) document.getElementById('np').value = data.np;
                
                // Try to fill standard "val_1" slots if keys exist (handling both simple and complex JSONs)
                // If the JSON came from the optimization tool, params are nested under 'params'.
                // If it came from here, they might be direct.
                
                let deltaVal, nelectronVal, bmagVal, asizeVal;

                if (data.params) { // Optimization tool format
                     if (data.params.delta) deltaVal = data.params.delta.value;
                     if (data.params.nelectron) nelectronVal = data.params.nelectron.value;
                     if (data.params.bmag) bmagVal = data.params.bmag.value;
                     if (data.params.asize) asizeVal = data.params.asize.value;
                } else { // Direct format (flat)
                    deltaVal = data.delta;
                    nelectronVal = data.nelectron;
                    bmagVal = data.bmag;
                    asizeVal = data.asize;
                }

                if (deltaVal !== undefined) document.getElementById('delta_val_1').value = deltaVal;
                if (nelectronVal !== undefined) document.getElementById('nelectron_val_1').value = nelectronVal;
                if (bmagVal !== undefined) document.getElementById('bmag_val_1').value = bmagVal;
                if (asizeVal !== undefined) document.getElementById('asize_val_1').value = asizeVal;
                
                e.target.value = ''; // Reset
                
            } catch (err) {
                alert('Error parsing JSON file: ' + err.message);
            }
        };
        reader.readAsText(file);
    });

    function getParamValues(paramName) {
        // Collect values from inputs named paramName_val_1 to _4
        const selectedParam = document.querySelector('input[name="study_param"]:checked').value;
        
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
                viewAngle: parseFloat(document.getElementById('viewAngle').value),
                height: parseFloat(document.getElementById('height').value),
                j1: parseInt(document.getElementById('j1').value),
                j2: parseInt(document.getElementById('j2').value),
                etr: parseFloat(document.getElementById('etr').value),
                np: parseFloat(document.getElementById('np').value),
                delta: getParamValues('delta'),
                nelectron: getParamValues('nelectron'),
                bmag: getParamValues('bmag'),
                asize: getParamValues('asize')
            };

            const apiUrl = 'http://localhost:8000/parameterImpact';

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
        
        resultsPanel.scrollIntoView({ behavior: 'smooth' });
    }
});
