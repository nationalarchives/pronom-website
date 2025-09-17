// describe("PRONOM View Format Spec", () => {
//     beforeEach(() => {
//         cy.visit("")
//         cy.get("a[href='/search']").click()
//     })
//
//     it("renders the summary section", () => {
//         cy.get("#search").type("fmt/1509")
//         cy.get("form[action='/results']").submit()
//         cy.get("h1.tna-heading-m").should("have.text", "Microsoft Visio Drawing")
//         cy.get("a[href='/edit/fmt/1509']").should("have.text", "Edit")
//         cy.contains(" Summary ").parent().find("button").should("have.attr", "aria-expanded", "true")
//         cy.get("#summary-content-1 > dl").should("have.class", "tna-dl")
//         const summaryFields = {};
//
//         cy.get('#summary-content-1 > dl > dt').each(dt => {
//             summaryFields[dt.text()] = dt.next('dd').text().trim();
//         }).then(_ => {
//             expect(summaryFields["Name"]).to.equal("Microsoft Visio Drawing")
//             expect(summaryFields["Version"]).to.equal("3")
//             expect(summaryFields["Identifiers"]).to.equal("MIME: application/vnd.visio, PUID: fmt/1509")
//             expect(summaryFields["Format Type"]).to.equal("Image (Vector)")
//             expect(summaryFields["Family"]).to.equal("")
//             expect(summaryFields["Disclosure"]).to.equal("")
//             expect(summaryFields["Description"]).to.equal("Microsoft Visio is a diagramming and vector graphics application and is part of the Microsoft Office family.")
//             expect(summaryFields["Note"]).to.equal("")
//             expect(summaryFields["Source"]).to.equal("The Church of Jesus Christ of Latter-Day Saints / The Church of Jesus Christ of Latter-Day Saints")
//             expect(summaryFields["Developed by"]).to.equal("Microsoft Corporation")
//             expect(summaryFields["Supported by"]).to.equal("Microsoft Corporation")
//         })
//
//     })
//
//     it("renders the containers section", () => {
//         cy.get("#search").type("fmt/1509")
//         cy.get("form[action='/results']").submit()
//         const containerSignaturesButton = cy.contains(" Container signatures ").parent().find("button")
//         containerSignaturesButton.should("have.attr", "aria-expanded", "false")
//         containerSignaturesButton.click()
//         containerSignaturesButton.should("have.attr", "aria-expanded", "true")
//
//         cy.get("#file-path-13090").should("have.text", "VisioDocument")
//         cy.get("#byteSequenceBOFoffset").should("have.text", "BOFoffset")
//
//         const containerFields = {}
//         cy.get('.tna-dl').last().find("dt").each(dt => {
//             containerFields[dt.text()] = dt.next('dd').text().trim();
//         }).then(_ => {
//             expect(containerFields["Min Frag Length"]).to.equal("0")
//             expect(containerFields["Position"]).to.equal("1")
//             expect(containerFields["Sub sequence min offset"]).to.equal("0")
//             expect(containerFields["Sub sequence max offset"]).to.equal("0")
//             expect(containerFields["Sequence"]).to.equal("'Visio (TM) Drawing'0D0A")
//             expect(containerFields["Right fragment"]).to.equal("Max offset 6 Min offset 6 Position 1")
//         })
//     })
//
//     it("renders the signature section", () => {
//         cy.get("#search").type("fmt/1177")
//         cy.get("form[action='/results']").submit()
//         const signaturesButton = cy.contains(" Signatures ").parent().find("button")
//         signaturesButton.should("have.attr", "aria-expanded", "false")
//         signaturesButton.click()
//         signaturesButton.should("have.attr", "aria-expanded", "true")
//
//         const signatureFields = {}
//         cy.get('#signatures-content-1 > dl > dt').each(dt => {
//             signatureFields[dt.text()] = dt.next('dd').text().trim();
//         }).then(_ => {
//             expect(signatureFields["Name"]).to.equal("Microstation Material Library")
//             expect(signatureFields["Description"]).to.equal("BOF: MV_AS--0")
//         })
//
//     })
//
// })
