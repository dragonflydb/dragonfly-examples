export const containsExactlyOneHashtag = (str?: string): boolean => {
    if (!str || str.trim() === '') {
        return false;
    }

    const openCount = (str.match(/\{/g) || []).length;
    const closeCount = (str.match(/\}/g) || []).length;

    const openIndex = str.indexOf('{');
    const closeIndex = str.indexOf('}');

    // 1. Exactly one opening brace.
    // 2. Exactly one closing brace.
    // 3. Opening brace must come before closing brace.
    return openCount === 1 && closeCount === 1 && openIndex < closeIndex;
}
