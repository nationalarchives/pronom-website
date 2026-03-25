describe("PRONOM View Format Spec", () => {
    beforeEach(() => {
        cy.visit("");
    });


    it("renders the summary section", () => {
        cy.visit("fmt/1509")
        cy.get("h1.tna-hgroup__title").should("have.text", "Microsoft Visio Drawing")
        const summaryFields: {[key: string]: string} = {};
        cy.get('.tna-dl--lined > dt').each(dt => {
            summaryFields[dt.text().trim()] = dt.next('dd').text().trim();
        }).then(_ => {
            console.log(summaryFields)
            expect(summaryFields["Name"]).to.equal("Microsoft Visio Drawing")
            expect(summaryFields["Version"]).to.equal("3")
            expect(summaryFields["Identifiers"]).to.equal("MIME: application/vnd.visio, PUID: fmt/1509")
            expect(summaryFields["Format Type"]).to.equal("Image (Vector)")
            expect(summaryFields["Description"]).to.equal("Microsoft Visio is a diagramming and vector graphics application and is part of the Microsoft Office family.")
            expect(summaryFields["Source"]).to.equal("The Church of Jesus Christ of Latter-Day Saints / The Church of Jesus Christ of Latter-Day Saints")
            expect(summaryFields["Developed by"]).to.equal("Microsoft Corporation")
            expect(summaryFields["Supported by"]).to.equal("Microsoft Corporation")
        })

    })

    it("renders the containers section", () => {
        cy.visit("fmt/1509")
        cy.get("#file-path-13090--1 > dd").should("have.text", "VisioDocument")
        cy.get("#byteSequence-13090-1 + p").should("have.text", "BOFoffset")

        const containerFields: {[key: string]: string} = {}
        cy.get('.tna-dl').last().find("dt").each(dt => {
            containerFields[dt.text()] = dt.next('dd').text().trim();
        }).then(_ => {
            expect(containerFields["Min Frag Length"]).to.equal("0")
            expect(containerFields["Position"]).to.equal("1")
            expect(containerFields["Sub sequence min offset"]).to.equal("0")
            expect(containerFields["Sub sequence max offset"]).to.equal("0")
            expect(containerFields["Sequence"]).to.equal("'Visio (TM) Drawing'0D0A")
            expect(containerFields["Right fragment"]).to.equal("Max offset 6 Min offset 6 Position 1")
        })
    })

    it("renders the signature section", () => {
        cy.visit("fmt/1177")

        cy.get("#internal-signatures-1559 > h3").should("have.text", "Microstation Material Library")
        cy.get("#signature-note-1559 + dd").should("have.text", "BOF: MV_AS--0")

        const signatureFields: {[key: string]: string} = {}

        cy.get('.tna-dl--lined > dt').each(dt => {
            signatureFields[dt.text()] = dt.next('dd').text().trim();
        }).then(_ => {
            expect(signatureFields["Min Frag Length"]).to.equal("Absolute from BOF")
            expect(signatureFields["Offset"]).to.equal("0")
            expect(signatureFields["Max offset"]).to.equal("0")
            expect(signatureFields["Byte Sequence"]).to.equal("4D565F41532D2D30")
            expect(signatureFields["Endianness"]).to.equal("None")
        })
    })

    it("renders the sidebar", () => {
        cy.visit("fmt/412")
        cy.get("#summary").should("have.text","Summary")
        cy.get("#relationships").should("have.text", "Relationships")
        cy.get("#container-signatures").should("have.text", "Container signatures")
        cy.get('[href="#container-signatures-1030"]').should("have.text", "Microsoft Word OOXML")
        cy.get('[href="#container-signatures-1040"]').should("have.text", "Microsoft Word OOXML (little endian unicode)")
        cy.get('[href="#container-signatures-1050"]').should("have.text", "Microsoft Word OOXML (big endian unicode)")
    })

    it("renders the relationships", () => {
        cy.visit("fmt/41")
        const relationships: {[key: string]: string} = {}
        cy.get("#relationships + dl > dd a").each(a => {
            relationships[a.attr("href") as string] = a.text()
        }).then(_ => {
            expect(relationships["/fmt/42"]).to.equal("JPEG File Interchange Format 1.00")
            expect(relationships["/fmt/43"]).to.equal("JPEG File Interchange Format 1.01")
            expect(relationships["/fmt/44"]).to.equal("JPEG File Interchange Format 1.02")
            expect(relationships["/fmt/112"]).to.equal("Still Picture Interchange File Format 1.0")
            expect(relationships["/x-fmt/390"]).to.equal("Exchangeable Image File Format (Compressed) 2.1")
            expect(relationships["/x-fmt/391"]).to.equal("Exchangeable Image File Format (Compressed) 2.2")
            expect(relationships["/x-fmt/398"]).to.equal("Exchangeable Image File Format (Compressed) 2.0")
            expect(relationships["/fmt/645"]).to.equal("Exchangeable Image File Format (Compressed) 2.21")
            expect(relationships["/fmt/1507"]).to.equal("Exchangeable Image File Format (Compressed) 2.3.x")
        })
    })
})
