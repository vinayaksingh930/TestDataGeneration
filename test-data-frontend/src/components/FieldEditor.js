import React, { useMemo } from 'react';
import allDataTypes from '../data/allDataTypes';
import { generateSample } from '../utils/generators';
import './FieldEditor.css';

export default function FieldEditor({
    field,
    onChange,
    onRemove,
    openTypeModal,
    context // optional: {mode:'single', index} or {mode:'table', tableIndex, fieldIndex}
}) {
    const preview = useMemo(() => {
        // prefer explicit example, then generator
        if (field.example) return field.example;
        return generateSample(field.type);
    }, [field.example, field.type]);

    const handleTypeChange = (v) => {
        onChange('type', v);
        const t = allDataTypes.find(x => x.id === v || x.name === v);
        if (t) {
            if (t.example) onChange('example', t.example);
            // rules: defaultRule or description
            onChange('rules', t.defaultRule || t.description || '');
        }
    };

    return (
        <div className="field-editor">
            <input
                type="text"
                className="fe-name"
                placeholder="Field Name"
                value={field.name}
                onChange={(e) => onChange('name', e.target.value)}
                required
            />

            <div className="fe-type-wrap">
                <select className="fe-type" value={field.type} onChange={(e) => handleTypeChange(e.target.value)}>
                    <optgroup label="Common types">
                        <option value="string">String</option>
                        <option value="integer">Integer</option>
                        <option value="float">Float</option>
                        <option value="boolean">Boolean</option>
                        <option value="email">Email</option>
                        <option value="phone">Phone</option>
                        <option value="date">Date</option>
                    </optgroup>
                    <optgroup label="All types">
                        {allDataTypes.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                    </optgroup>
                </select>
                <button type="button" className="fe-choose" onClick={openTypeModal}>Choose...</button>
            </div>

            <input type="text" className="fe-rules" placeholder="Rules" value={field.rules || ''} onChange={(e) => onChange('rules', e.target.value)} />
            <input type="text" className="fe-example" placeholder="Example" value={field.example || ''} onChange={(e) => onChange('example', e.target.value)} />

            <div className="fe-preview">Preview: <code>{preview}</code></div>

            {onRemove && (
                <button type="button" className="fe-remove" onClick={onRemove}>✕</button>
            )}
        </div>
    );
}
