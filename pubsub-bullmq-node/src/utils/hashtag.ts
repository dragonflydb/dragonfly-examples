export const containsHashtag = (str: string): boolean => {
    const openCount = (str.match(/\{/g) || []).length;
    const closeCount = (str.match(/\}/g) || []).length;
    const openIndex = str.indexOf('{');
    const closeIndex = str.indexOf('}');
    return openCount === 1 && closeCount === 1 && openIndex < closeIndex;
}
