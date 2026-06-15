describe("PRONOM Format XML", () => {
  it("renders the xml for a given puid", () => {
    cy.request({
      url: "/fmt/1.xml",
    }).then((apiResponse) => {
      const body = apiResponse.body;
      expect(body).to.contain(
        '<PRONOM-Report xmlns="http://pronom.nationalarchives.gov.uk">',
      );
      expect(body).to.contain("<FormatID>735</FormatID>");
      expect(body).to.contain("<FormatName>Broadcast WAVE</FormatName>");
    });
  });
});
