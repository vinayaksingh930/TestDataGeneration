const bankingDataTypes = [
    {
        id: 'bank_name',
        name: 'Bank Name',
        category: 'Banking',
        description: 'Common bank names used in the region (e.g., SBI, HDFC, ICICI).',
        example: 'STATE BANK OF INDIA',
        defaultRule: ''
    },
    {
        id: 'ifsc',
        name: 'IFSC Code (India)',
        category: 'Banking',
        description: '11-character Indian bank branch identifier (e.g., SBIN0000456).',
        example: 'SBIN0000456',
        defaultRule: '^[A-Z]{4}0[A-Z0-9]{6}$'
    },
    {
        id: 'pan',
        name: 'PAN Number (India)',
        category: 'Banking',
        description: '10-character Permanent Account Number format e.g., ABCDE1234F.',
        example: 'ABCDE1234F',
        defaultRule: '[A-Z]{3}[A-Z][A-Z][0-9]{4}[A-Z]'
    },
    {
        id: 'account_number',
        name: 'Bank Account Number',
        category: 'Banking',
        description: 'A numeric bank account number – length varies by bank.',
        example: '012345678901',
        defaultRule: 'digits, length 9-18'
    },
    {
        id: 'ifsc_branch_address',
        name: 'Branch Address',
        category: 'Banking',
        description: 'Physical address of the bank branch.',
        example: 'MG Road, Bengaluru, Karnataka',
        defaultRule: ''
    },
    {
        id: 'swift_bic',
        name: 'SWIFT / BIC',
        category: 'Banking',
        description: 'SWIFT/BIC codes for international transfers (8 or 11 chars).',
        example: 'HDFCINBBXXX',
        defaultRule: ''
    },
    {
        id: 'iban',
        name: 'IBAN',
        category: 'Banking',
        description: 'International Bank Account Number used in many countries.',
        example: 'GB29NWBK60161331926819',
        defaultRule: ''
    },
    {
        id: 'routing_number',
        name: 'Routing Number (ABA)',
        category: 'Banking',
        description: 'US bank routing number (9 digits).',
        example: '011000138',
        defaultRule: '^[0-9]{9}$'
    },
    {
        id: 'micr',
        name: 'MICR Code',
        category: 'Banking',
        description: 'Magnetic ink character recognition code used in India for cheques (9 digits).',
        example: '110002001',
        defaultRule: '^[0-9]{9}$'
    },
    {
        id: 'account_type',
        name: 'Account Type',
        category: 'Banking',
        description: 'Type of account: Savings, Current, Salary, NRE, NRO.',
        example: 'Savings',
        defaultRule: 'one of [Savings, Current, Salary, NRE, NRO]'
    },
    {
        id: 'pan_masked',
        name: 'PAN (masked)',
        category: 'Banking',
        description: 'Masked PAN for privacy, e.g., AB***234F.',
        example: 'AB***234F',
        defaultRule: ''
    },
    {
        id: 'ifsc_lookup',
        name: 'IFSC (with branch)',
        category: 'Banking',
        description: 'IFSC with a friendly branch name included.',
        example: 'SBIN0000456 — MG ROAD BRANCH',
        defaultRule: ''
    }
];

export default bankingDataTypes;
