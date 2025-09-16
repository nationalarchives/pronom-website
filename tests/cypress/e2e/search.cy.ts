describe("PRONOM Search Spec", () => {
  beforeEach(() => {
    cy.visit("");
    cy.get("main a[href='/search']").click();
  });

  it("renders the search page", () => {
    cy.location().should((location: Location) => {
      expect(location.pathname).to.eq("/search");
    });
    cy.get("#search").should("exist");
    cy.contains("Search PRONOM").should("exist");
  });

  it("submits a search if the search is not a puid", () => {
    const checkSearchLinks = (puid: string, name: string): void => {
      const fmt: Cypress.Chainable<JQuery<HTMLElement>> = cy
        .get(`a[href='${puid}']`)
        .last();
      fmt.should("have.text", puid);
      fmt.parent().next().should("have.text", name);
    };
    cy.get("#search").type("docx");
    cy.intercept("GET", "/results?q=*").as("results");
    cy.get("form[action='/results']").submit();
    cy.wait("@results").should(({ request, response }) => {
      expect(request.query["q"]).to.equal("docx");
      expect(response.statusCode).to.equal(200);
    });
    checkSearchLinks("fmt/1571", "ISDOCX Information System Document");
    checkSearchLinks("fmt/1827", "DOCX Strict OOXML Document");
    checkSearchLinks("fmt/1568", "ISDOCX Information System Document");
  });

  it("redirects if the search is a valid puid", () => {
    cy.get("#search").type("fmt/1");
    cy.intercept("GET", "/results?q=*").as("results");
    cy.get("form[action='/results']").submit();
    cy.wait("@results").should(({ _, response }) => {
      expect(response.statusCode).to.equal(302);
      expect(response.headers["location"]).to.equal("fmt/1");
    });
  });

  it("returns no results if no results are found", () => {
    cy.get("#search").type("thisstringdoesnotexist");
    cy.intercept("GET", "/results?q=*").as("results");
    cy.get("form[action='/results']").submit();
    cy.wait("@results").its("response.statusCode").should("eq", 200);
    cy.get("h1").should("have.text", "No results found");
  });

  it("returns no results if the search is a non-existent puid", () => {
    cy.get("#search").type("fmt/12345678");
    cy.intercept("GET", "/results?q=*").as("results");
    cy.get("form[action='/results']").submit();
    cy.wait("@results").its("response.statusCode").should("eq", 200);
    cy.get("h1").should("have.text", "No results found");
  });
});
