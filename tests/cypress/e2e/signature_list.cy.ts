type Signature = {
    name: string,
    location: string
}
type AllSignatures = {
    signatures: Array<Signature>
    container_signatures: Array<Signature>
}
describe('PRONOM Signature List Spec', () => {
    beforeEach(() => {
        cy.visit('')
        cy.get("main a[href='/signature_list']").click()
    })
    it('renders the signature files page', () => {
        cy.request<AllSignatures>('https://d21gi86t6uhf68.cloudfront.net/signatures.json').then((res: Cypress.Response<AllSignatures>) => {
            const checkSignatures: (signatures: Array<Signature>) => void = signatures => {
                for (const {location, name} of signatures) {
                    cy.get(`a[href='${location}`).should("have.html", name)
                }
            }

            checkSignatures(res.body.signatures)
            checkSignatures(res.body.container_signatures)
        })
    })
});