import {checkSelectInput, checkTextInput, jsonFromForm} from "./utils";

describe('PRONOM Add Organisation Spec', () => {
    beforeEach(() => {
        cy.visit('')
        cy.get("a[href='/contribute']").click()
        cy.get("a[href='/actor/add']").click()
    })


    it('renders the add signature form', () => {
        cy.contains('Add a new organisation').should('have.class', 'tna-heading-l')
        checkTextInput('Name')
        checkTextInput('Address')
        checkSelectInput('Country', '')
        checkTextInput('Company Website')
        checkTextInput('Support Website')
    })

    it('should submit the form for a new signature', () => {
        cy.get('#name').type('Test organisation name')
        cy.get('#address').type('Test address')
        cy.get('#addressCountry').select('Antarctica')
        cy.get('#companyWebsite').type('https://example.com/company')
        cy.get('#supportWebsite').type('https://example.com/support')

        cy.intercept('POST', '/submissions').as('submissions')
        cy.get("form[action='/submissions']").submit()
        cy.wait('@submissions').should(({ request, response }) => {
            const jsonBody: { [p: string]: string } = jsonFromForm(request)

            expect(jsonBody.submissionType).to.equal('add-actor')
            expect(jsonBody.name).to.equal('Test organisation name')
            expect(jsonBody.address).to.equal('Test address')
            expect(jsonBody.addressCountry).to.equal('Antarctica')
            expect(jsonBody.companyWebsite).to.equal('https://example.com/company')
            expect(jsonBody.supportWebsite).to.equal('https://example.com/support')
            expect(response.statusCode).to.equal(302)
            expect(response.headers['location']).to.equal('/submissions-received/1')
        })
    })

    it('should render the submission received page', () => {
        cy.get("form[action='/submissions']").submit()
        cy.get("a[href='https://github.com/nationalarchives/pronom-signatures/pull/1']").should('exist')
    })

})
