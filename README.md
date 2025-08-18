# python-prints

A Node.js library for working with printers using a Python-powered backend.  
Currently supports **Windows**.

---

## Installation

```bash
npm install python-prints
```


## Usage

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
```

## Notes
- The file path must be absolute.
- Works only on Windows for now.
- Requires no Python installation (bundled binary included).


## Contact | Feedback | Suggestion
if you need anything or you want to give me a feedback or a suggestion, you can contact me on my email (mr.mhmd.almalki@gmail.com)