import {checkSelectInput, checkTextInput, checkTextValue, jsonFromForm} from "./utils";

describe.skip('PRONOM Edit Organisation Spec', () => {
    beforeEach(() => {
        cy.visit('/actor/edit/93')
    })

    it('renders the add signature form', () => {
        cy.contains('Add a new organisation').should('have.class', 'tna-heading-l')
        checkTextValue('Name', 'Microsoft Corporation')
        checkTextValue('Address', 'One Microsoft Way, Redmond, WA, 98052-6399')
        checkSelectInput('Country', 'United States')
        checkTextValue('Company Website', 'www.microsoft.com/')
        checkTextValue('Support Website', 'support.microsoft.com/')
    })

    it('should submit the form for a new signature', () => {
        cy.get('#name').clear()
        cy.get('#name').type('New organisation name')
        cy.get('#addressCountry').select('United Kingdom')

        cy.intercept('POST', '/submissions').as('submissions')
        cy.get("form[action='/submissions']").submit()
        cy.wait('@submissions').should(({ request, response }) => {
            const jsonBody: { [p: string]: string } = jsonFromForm(request)

            expect(jsonBody.submissionType).to.equal('edit-actor')
            expect(jsonBody.name).to.equal('New organisation name')
            expect(jsonBody.address).to.equal('One Microsoft Way, Redmond, WA, 98052-6399')
            expect(jsonBody.addressCountry).to.equal('United Kingdom')
            expect(jsonBody.companyWebsite).to.equal('www.microsoft.com/')
            expect(jsonBody.supportWebsite).to.equal('support.microsoft.com/')
            expect(response.statusCode).to.equal(302)
            expect(response.headers['location']).to.equal('/submissions-received/1')
        })
    })

    it('should render the submission received page', () => {
        cy.get("form[action='/submissions']").submit()
        cy.get("a[href='https://github.com/nationalarchives/pronom-signatures/pull/1']").should('exist')
    })

})