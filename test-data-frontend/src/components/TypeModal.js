import React, { useState, useMemo } from 'react';
import './TypeModal.css';

export default function TypeModal({ show = false, onClose = () => { }, types = [], onSelect = () => { } }) {
    const [query, setQuery] = useState('');
    const [category, setCategory] = useState('All');

    const categories = useMemo(() => {
        const map = { All: types.length };
        types.forEach(t => {
            const c = t.category || 'Uncategorized';
            map[c] = (map[c] || 0) + 1;
        });
        return map;
    }, [types]);

    const filtered = useMemo(() => {
        const q = query.trim().toLowerCase();
        return types.filter(t => {
            if (category !== 'All' && (t.category || 'Uncategorized') !== category) return false;
            if (!q) return true;
            return (t.name + ' ' + (t.description || '') + ' ' + (t.category || '')).toLowerCase().includes(q);
        });
    }, [query, types, category]);

    if (!show) return null;

    return (
        <div className="type-modal-backdrop" onClick={onClose}>
            <div className="type-modal" onClick={(e) => e.stopPropagation()}>
                <div className="type-modal-header">
                    <h3>Choose a Type</h3>
                    <button className="close-btn" onClick={onClose}>✕</button>
                </div>

                <div className="type-modal-body">
                    <div className="type-categories">
                        {Object.keys(categories).map(cat => (
                            <div
                                key={cat}
                                className={`type-category-item ${category === cat ? 'active' : ''}`}
                                onClick={() => setCategory(cat)}
                            >
                                <div className="cat-name">{cat}</div>
                                <div className="cat-count">{categories[cat]}</div>
                            </div>
                        ))}
                    </div>

                    <div className="type-content">
                        <div className="type-modal-search">
                            <input
                                placeholder="Search types... e.g., IFSC, PAN, Account"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                            />
                        </div>

                        <div className="type-list">
                            {filtered.length === 0 && <div className="no-results">No results</div>}
                            {filtered.map((t) => (
                                <div key={t.id} className="type-card" onClick={() => onSelect(t)}>
                                    <div className="type-card-left">
                                        <strong className="type-name">{t.name}</strong>
                                        <div className="type-category">{t.category}</div>
                                    </div>
                                    <div className="type-card-right">
                                        <div className="type-desc">{t.description}</div>
                                        {t.example && <div className="type-example">Example: <code>{t.example}</code></div>}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
