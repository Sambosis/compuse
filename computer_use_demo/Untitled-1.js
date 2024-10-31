// Read the file content
const fileContent = await window.fs.readFile('paste.txt', { encoding: 'utf8' });

// Function to extract links using regex
function extractLinks(content) {
    const linkRegex = /<a[^>]*?href=["']([^"']*?)["'][^>]*?>([^<]*?)<\/a>/g;
    const links = [];
    let match;

    while ((match = linkRegex.exec(content)) !== null) {
        // Extract additional attributes
        const fullTag = match[0];
        const classMatch = fullTag.match(/class=["']([^"']*?)["']/);
        const styleMatch = fullTag.match(/style=["']([^"']*?)["']/);
        const idMatch = fullTag.match(/id=["']([^"']*?)["']/);

        const linkInfo = {
            url: match[1],
            displayName: match[2].trim(),
            class: classMatch ? classMatch[1] : null,
            style: styleMatch ? styleMatch[1] : null,
            id: idMatch ? idMatch[1] : null
        };

        // Only include links that have either a display name or URL
        if (linkInfo.displayName || linkInfo.url) {
            links.push(linkInfo);
        }
    }
    return links;
}

const linkData = extractLinks(fileContent);

console.log(`Total links found: ${linkData.length}`);
console.log('\nSample of first few links:');
console.log(JSON.stringify(linkData.slice(0, 5), null, 2));

// Let's also count links by type
const urlTypes = {};
linkData.forEach(link => {
    const urlType = link.url.split('?')[0];
    urlTypes[urlType] = (urlTypes[urlType] || 0) + 1;
});

console.log('\nURL types distribution:');
console.log(JSON.stringify(urlTypes, null, 2));