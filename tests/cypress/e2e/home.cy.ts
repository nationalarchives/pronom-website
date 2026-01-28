describe("PRONOM Home Spec", () => {
  beforeEach(() => {
    cy.visit("");
  });

  it("displays the expected links", () => {
    cy.get("a[href='/signature-list']")
      .first()
      .should("contain.text", "DROID Signature Files");
  });
});
