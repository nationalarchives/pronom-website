describe.skip("PRONOM Contribute Spec", () => {
  beforeEach(() => {
    cy.visit("");
    cy.get("main a[href='/contribute']").click();
  });

  it("displays the expected links", () => {
    cy.get("a[href='/add']").last().should("have.text", "Add a new signature");
    cy.get("a[href='/actor/add']")
      .last()
      .should("have.text", "Add a new organisation");
    cy.get("a[href='https://github.com/nationalarchives/pronom-signatures/']")
      .last()
      .should("have.text", "View signatures on GitHub");
  });
});
