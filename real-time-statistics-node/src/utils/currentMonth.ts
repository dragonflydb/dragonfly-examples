// Utility function to construct a key for the current month.
export const keyForCurrMonth = (prefix: String): string => {
    const now = new Date();
    return keyForMonth(prefix, now);
};

// Utility function to construct a key for a given month.
export const keyForMonth = (prefix: String, date: Date): string => {
    // Zero-fill the month.
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    return `${prefix}:${year}:${month}`;
};
