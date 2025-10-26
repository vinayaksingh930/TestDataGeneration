import React, { useState } from 'react';
import './App.css';

function App() {
    const [fields, setFields] = useState([{ name: '', type: 'string', rules: '', example: '' }]);
    const [numRecords, setNumRecords] = useState(5);
    const [correctNumRecords, setCorrectNumRecords] = useState(5);
    const [wrongNumRecords, setWrongNumRecords] = useState(0);
    const [additionalRules, setAdditionalRules] = useState('');
    const [response, setResponse] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [viewMode, setViewMode] = useState('json'); // 'json' or 'csv'

    const addField = () => {
        setFields([...fields, { name: '', type: 'string', rules: '', example: '' }]);
    };

    const removeField = (index) => {
        const newFields = fields.filter((_, i) => i !== index);
        setFields(newFields);
    };

    const updateField = (index, key, value) => {
        const updatedFields = [...fields];
        updatedFields[index][key] = value;
        setFields(updatedFields);
    };

    // Convert JSON data to CSV format
    const convertToCSV = (data) => {
        if (!data || data.length === 0) return '';

        // Get headers from the first object
        const headers = Object.keys(data[0]);
        const csvHeaders = headers.join(',');

        // Convert each object to a CSV row
        const csvRows = data.map(obj => {
            return headers.map(header => {
                const value = obj[header];
                // Escape values that contain commas or quotes
                if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                    return `"${value.replace(/"/g, '""')}"`;
                }
                return value;
            }).join(',');
        });

        return [csvHeaders, ...csvRows].join('\n');
    };

    // Download CSV file
    const downloadCSV = () => {
        if (!response || !response.data) return;

        const csv = convertToCSV(response.data);
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'test-data.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }; const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setResponse(null);

        try {
            const res = await fetch('http://localhost:8000/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    schema_fields: fields.filter(f => f.name),
                    num_records: parseInt(numRecords),
                    correct_num_records: parseInt(correctNumRecords),
                    wrong_num_records: parseInt(wrongNumRecords),
                    additional_rules: additionalRules || undefined
                }),
            });

            if (!res.ok) {
                throw new Error(`Error: ${res.status}`);
            }

            const data = await res.json();
            setResponse(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="App">
            <h1>Test Data Generator</h1>

            <form onSubmit={handleSubmit}>
                <div className="form-section">
                    <h2>Schema Fields</h2>
                    {fields.map((field, index) => (
                        <div key={index} className="field-row">
                            <input
                                type="text"
                                placeholder="Field Name"
                                value={field.name}
                                onChange={(e) => updateField(index, 'name', e.target.value)}
                                required
                            />
                            <select
                                value={field.type}
                                onChange={(e) => updateField(index, 'type', e.target.value)}
                            >
                                <option value="string">String</option>
                                <option value="integer">Integer</option>
                                <option value="float">Float</option>
                                <option value="boolean">Boolean</option>
                                <option value="email">Email</option>
                                <option value="phone">Phone</option>
                                <option value="date">Date</option>
                            </select>
                            <input
                                type="text"
                                placeholder="Rules (optional)"
                                value={field.rules}
                                onChange={(e) => updateField(index, 'rules', e.target.value)}
                            />
                            <input
                                type="text"
                                placeholder="Example (optional)"
                                value={field.example}
                                onChange={(e) => updateField(index, 'example', e.target.value)}
                            />
                            {fields.length > 1 && (
                                <button type="button" onClick={() => removeField(index)} className="remove-btn">
                                    ✕
                                </button>
                            )}
                        </div>
                    ))}
                    <button type="button" onClick={addField} className="add-btn">
                        + Add Field
                    </button>
                </div>

                <div className="form-section">
                    <label>
                        Total Number of Records:
                        <input
                            type="number"
                            min="1"
                            max="100"
                            value={numRecords}
                            onChange={(e) => setNumRecords(e.target.value)}
                        />
                    </label>
                </div>
                <div className="form-section">
                    <label>
                        Number of Correct Records:
                        <input
                            type="number"
                            min="0"
                            max={numRecords}
                            value={correctNumRecords}
                            onChange={(e) => setCorrectNumRecords(e.target.value)}
                        />
                    </label>
                </div>


                <div className="form-section">
                    <label>
                        Number of Wrong Records:
                        <input
                            type="number"
                            min="0"
                            max={numRecords}
                            value={wrongNumRecords}
                            onChange={(e) => setWrongNumRecords(e.target.value)}
                        />
                    </label>
                </div>

                <div className="form-section">
                    <label>
                        Additional Rules (optional):
                        <textarea
                            value={additionalRules}
                            onChange={(e) => setAdditionalRules(e.target.value)}
                            placeholder="Any additional context or rules..."
                            rows="3"
                        />
                    </label>
                </div>

                <button type="submit" disabled={loading} className="submit-btn">
                    {loading ? 'Generating...' : 'Generate Data'}
                </button>
            </form>

            {error && (
                <div className="error">
                    <h3>Error:</h3>
                    <p>{error}</p>
                </div>
            )}

            {response && (
                <div className="response">
                    <h2>Generated Data ({response.count} records)</h2>

                    <div className="view-controls">
                        <button
                            className={viewMode === 'json' ? 'active' : ''}
                            onClick={() => setViewMode('json')}
                        >
                            JSON View
                        </button>
                        <button
                            className={viewMode === 'csv' ? 'active' : ''}
                            onClick={() => setViewMode('csv')}
                        >
                            CSV View
                        </button>
                        <button onClick={downloadCSV} className="download-btn">
                            Download CSV
                        </button>
                    </div>

                    <div className="data-table">
                        {viewMode === 'json' ? (
                            <pre>{JSON.stringify(response.data, null, 2)}</pre>
                        ) : (
                            <pre>{convertToCSV(response.data)}</pre>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;
