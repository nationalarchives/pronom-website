describe("PRONOM Home Spec", () => {
  beforeEach(() => {
    cy.visit("");
  });

  it("displays the expected links", () => {
    cy.get("a[href='/signature-list']")
      .first()
      .should("contain.text", "View DROID signature files");
  });

  it("renders the search box", () => {
    cy.get("#search").should("exist");
    cy.contains("Search PRONOM").should("exist");
  });

  it("submits a search if the search is not a puid", () => {
    const checkSearchLinks = (puid: string, name: string): void => {
      const fmt: Cypress.Chainable<JQuery<HTMLElement>> = cy
        .get(`a[href='${puid}']`)
        .last();
      fmt.should("have.text", name);
    };
    cy.get("#search").type("docx");
    cy.intercept("GET", "/results?q=*").as("results");
    cy.get("form[action='/results']").submit();
    cy.wait("@results").should(({ request, response }) => {
      expect(request.query["q"]).to.equal("docx");
      if (response) {
        expect(response.statusCode).to.equal(200);
      }
    });
    checkSearchLinks("fmt/1571", "ISDOCX Information System Document 6.0.1");
    checkSearchLinks("fmt/1827", "DOCX Strict OOXML Document 2007 onwards");
    checkSearchLinks("fmt/1568", "ISDOCX Information System Document 5.x");
  });

  it("submits a an extension search if the search starts with a dot", () => {
    const checkSearchLinks = (puid: string, name: string): void => {
      const fmt: Cypress.Chainable<JQuery<HTMLElement>> = cy
          .get(`a[href='${puid}']`)
          .last();
      fmt.should("have.text", name);
    };
    cy.get("#search").type(".js");
    cy.get("form[action='/results']").submit();
    cy.get(".tna-card__heading").should("have.length", 1)
    cy.get("a[href='x-fmt/423']").should("have.text", "JavaScript file")
  });

  it("redirects if the search is a valid puid", () => {
    cy.get("#search").type("fmt/1");
    cy.intercept("GET", "/results?q=*").as("results");
    cy.get("form[action='/results']").submit();
    cy.wait("@results").should(({ _, response }) => {
      if (response) {
        expect(response.statusCode).to.equal(302);
        expect(response.headers["location"]).to.equal("fmt/1");
      }
    });
  });

  it("returns no results if no results are found", () => {
    cy.get("#search").type("thisstringdoesnotexist");
    cy.intercept("GET", "/results?q=*").as("results");
    cy.get("form[action='/results']").submit();
    cy.wait("@results").its("response.statusCode").should("eq", 200);
    cy.get(".tna-aside > h2.tna-heading-m").should(
      "have.text",
      "No results found",
    );
  });

  it("returns no results if the search is a non-existent puid", () => {
    cy.get("#search").type("fmt/12345678");
    cy.intercept("GET", "/results?q=*").as("results");
    cy.get("form[action='/results']").submit();
    cy.wait("@results").its("response.statusCode").should("eq", 200);
    cy.get(".tna-aside > h2.tna-heading-m").should(
      "have.text",
      "No results found",
    );
  });
});
