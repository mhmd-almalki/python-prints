# python-prints

A Node.js library for working with printers using a Python-powered backend.  
Currently supports **Windows**.

---

## Installation

```bash
npm install python-prints



```js
const { list, setDefault, printPdf } = require("python-prints");

async function run() {
  try {
    // List available printers
    const printers = await list();
    console.log("Printers:", printers);

    // Set default printer
    await setDefault("My_Printer_Name");

    // Print a PDF file (absolute path required)
    const result = await printPdf("C:\\path\\test.pdf", {
      printer: "My_Printer_Name", // you do not need to add this , it will use the default printer
      copies: 1,
    });

    console.log("Print result:", result);
  } catch (err) {
    console.error("Error:", err.message);
  }
}

run();


