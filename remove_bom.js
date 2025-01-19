const fs = require('fs');
    const path = require('path');

    function removeBomFromFile(filePath) {
      const fullPath = path.resolve(filePath);
      try {
        const data = fs.readFileSync(fullPath);
        if (data.length >= 3 && data[0] === 0xef && data[1] === 0xbb && data[2] === 0xbf) {
          console.log(`BOM found and removed from ${filePath}`);
          fs.writeFileSync(fullPath, data.slice(3));
        } else {
          console.log(`No BOM found in ${filePath}`);
        }
      } catch (err) {
        console.error(`Error processing file ${filePath}: ${err}`);
      }
    }

    // Remove BOM from specified files
    removeBomFromFile('main.py');
    removeBomFromFile('pdf_processor/processor.py');
