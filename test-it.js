const { list, setDefault, printPdf } = require('./index.js');

(async () => {
    try {
        const pdfPath = __dirname + "/test.pdf";

        // list printers
        const { printers, default: currentDefault } = await list();
        console.log("Printers:", printers);
        console.log("Default :", currentDefault || "(none)");

        if (!printers.length) throw new Error("No printers found");

        // pick printer (default or first one)
        const selected = currentDefault || printers[0];

        // set default
        console.log(`Setting default printer to: ${selected}`);
        await setDefault(selected);

        // print
        console.log(`Printing ${pdfPath} on ${selected} ...`);
        const result = await printPdf(pdfPath, { printer: selected });

        console.log("✅ Done:", result.message || "Success");
    } catch (e) {
        console.error("❌ Error:", e.message || e);
    }
})();
