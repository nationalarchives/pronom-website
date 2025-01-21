import {checkSelectInput, checkTextInput, checkTextValue, jsonFromForm} from "./utils";

describe('PRONOM Edit Signature Spec', () => {
    beforeEach(() => {
      cy.visit('/edit/fmt/2008')
    })

    const description = 'QuarkXPress is destop publishing software for creating and editing page layouts that can be run on Mac and Windows operating systems. It was first released in 1987. It can be used to creating a variety of layouts, from single-page flyers to multi-media projects required for magazines, newspapers and catalogues. Versions 1-3 were available on Macintosh only, from version 3.1 a common signature is used.'

    const checkTables: (className: string, expected: { type: string; value: string }[]) => void = (className, expected) => {
        cy.get(`.${className}-row`).each((identifierRow, idx) => {
            const tableData = identifierRow.children()
            const expectedIdentifier = expected[idx]
            expect(tableData[0].innerText).to.equal(expectedIdentifier.type)
            expect(tableData[1].innerText).to.equal(expectedIdentifier.value)
        })
    }


    it('renders the edit signature form', () => {
        checkTextValue('Your Name', '')
        checkTextValue('Change description', '')
        cy.contains('Format details').should('have.class', 'tna-heading-l')
        checkTextValue('Format Name', 'QuarkXPress Project')
        checkTextValue('Family', '')
        checkSelectInput('Disclosure', '')
        checkTextValue('Description', description)
        checkTextValue('Format Type', 'Presentation')
        checkTextValue('Note', '')
        checkSelectInput('Format developed by', '91')
        checkSelectInput('Format supported by', '91')
        const expectedIdentifiers = [{'type': 'MIME', 'value': 'application/vnd.Quark.QuarkXPress'}, {'type': 'PUID', 'value': 'fmt/2008'}]
        checkTables('identifier', expectedIdentifiers)
        const expectedRelationships = [{'type': 'Has priority over', 'value': 'x-fmt/182'}, {'type': 'Is subsequent version of', 'value': 'fmt/2007'}]
        checkTables('relationship', expectedRelationships)
        checkSelectInput('Format developed by', '91')
        checkSelectInput('Format supported by', '91')
        cy.contains('Identifiers').should('have.class', 'tna-heading-l')
        cy.contains('Relationships').should('have.class', 'tna-heading-l')
    })

    it('should submit the form for an edited signature', () => {
        cy.get('#formatName').clear()
        cy.get('#formatName').type('A different name')
        cy.get('#disclosure').select('Partial')
        cy.intercept('POST', '/submissions').as('submissions')
        cy.get("form[action='/submissions']").submit()
        cy.wait('@submissions').should(({ request, response }) => {
            const jsonBody = jsonFromForm(request)

            expect(jsonBody.submissionType).to.equal('edit-format')
            expect(jsonBody.contributorName).to.equal('')
            expect(jsonBody.changeDescription).to.equal('')
            expect(jsonBody.formatName).to.equal('A different name')
            expect(jsonBody.formatFamilies).to.equal('')
            expect(jsonBody.formatDisclosure).to.equal('Partial')
            expect(jsonBody.formatDescription).to.equal(description)
            expect(jsonBody.formatTypes).to.equal('Presentation')
            expect(jsonBody.formatNote).to.equal('')
            expect(jsonBody.developedBy).to.equal('91')
            expect(jsonBody.supportedBy).to.equal('91')
            expect(response.statusCode).to.equal(302)
            expect(response.headers['location']).to.equal('/submissions-received/1')
        })
    })

    it('should render the submission received page', () => {
        cy.get("form[action='/submissions']").submit()
        cy.get("a[href='https://github.com/nationalarchives/pronom-signatures/pull/1']").should('exist')
    })

})  
