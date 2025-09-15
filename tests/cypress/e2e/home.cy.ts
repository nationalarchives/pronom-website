describe('PRONOM Home Spec', () => {
  beforeEach(() => {
    cy.visit('')
  })

  it('displays the expected links', () => {
    cy.get("a[href='/search']").last().should('have.text', 'Search PRONOM')
    cy.get("a[href='/signature-list']").last().should('have.text', 'View signature files')
  })
})