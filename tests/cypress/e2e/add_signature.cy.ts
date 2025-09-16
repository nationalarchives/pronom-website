import { checkSelectInput, checkTextInput, jsonFromForm } from "./utils";

describe.skip("PRONOM Add Signature Spec", () => {
  beforeEach(() => {
    cy.visit("");
    cy.get("main a[href='/contribute']").click();
    cy.get("main a[href='/add']").click();
  });

  const checkInputTables: (selectId: string, textId: string) => void = (
    selectId,
    textId,
  ) => {
    const selectElement = cy.get(`#${selectId}`);
    selectElement.should("have.class", "tna-select");
    selectElement.should("have.value", "");
    selectElement.closest("table").should("have.class", "tna-table--full");

    const textElement = cy.get(`#${textId}`);
    textElement.should("have.class", "tna-text-input");
    textElement.should("have.value", "");
    textElement.closest("table").should("have.class", "tna-table--full");
  };

  it("renders the add signature form", () => {
    checkTextInput("Your Name");
    checkTextInput("Change description");
    cy.contains("Format details").should("have.class", "tna-heading-l");
    checkTextInput("Format Name");
    checkTextInput("Family");
    checkSelectInput("Disclosure", "");
    checkTextInput("Description");
    checkTextInput("Format Type");
    checkTextInput("Note");
    checkSelectInput("Format developed by", "0");
    checkSelectInput("Format supported by", "0");
    cy.contains("Identifiers").should("have.class", "tna-heading-l");
    checkInputTables("identifierType", "identifierText");
    cy.contains("Relationships").should("have.class", "tna-heading-l");
    checkInputTables("relationshipType", "relatedFormatName");
    cy.contains("Signatures").should("have.class", "tna-heading-l");
    checkSelectInput("Position Type", "");
    checkTextInput("Max Offset");
    checkTextInput("Byte Sequence");
    checkSelectInput("Endianness", "");
    checkTextInput("Signature Name");
    checkTextInput("Signature Note");
  });

  it("should submit the form for a new signature", () => {
    cy.get("#name").type("Test name");
    cy.get("#changeDescription").type("A description");
    cy.get("#formatName").type("Test format name");
    cy.get("#families").type("Test family");
    cy.get("#disclosure").select("Full");
    cy.get("#description").type("Description");
    cy.get("#formatTypes").type("Format type");
    cy.get("#formatNote").type("Format note");
    cy.get("#developedBy").select("18");
    cy.get("#supportedBy").select("18");
    cy.get("#identifierType").select("PUID");
    cy.get("#identifierText").type("fmt/12345");
    cy.get("#relationshipType").select("Has priority over");
    cy.get("#relatedFormatName").type("fmt/12345");
    cy.get("#signature-positionType").select("Variable");
    cy.get("#signature-offset").type("0");
    cy.get("#signature-maxOffset").type("0");
    cy.get("#signature-byteSequence").type("ABCDE");
    cy.get("#signature-endianness").select("Little-endian");
    cy.get("#signature-name").type("Signature name");
    cy.get("#signature-note").type("Signature note");
    cy.intercept("POST", "/submissions").as("submissions");
    cy.get("form[action='/submissions']").submit();
    cy.wait("@submissions").should(({ request, response }) => {
      const jsonBody = jsonFromForm(request);

      expect(jsonBody.submissionType).to.equal("add-format");
      expect(jsonBody.contributorName).to.equal("Test name");
      expect(jsonBody.changeDescription).to.equal("A description");
      expect(jsonBody.formatName).to.equal("Test format name");
      expect(jsonBody.formatFamilies).to.equal("Test family");
      expect(jsonBody.formatDisclosure).to.equal("Full");
      expect(jsonBody.formatDescription).to.equal("Description");
      expect(jsonBody.formatTypes).to.equal("Format type");
      expect(jsonBody.formatNote).to.equal("Format note");
      expect(jsonBody.developedBy).to.equal("18");
      expect(jsonBody.supportedBy).to.equal("18");
      expect(jsonBody.identifierType).to.equal("PUID");
      expect(jsonBody.identifierText).to.equal("fmt/12345");
      expect(jsonBody.relationshipType).to.equal("Has priority over");
      expect(jsonBody.relatedFormatName).to.equal("fmt/12345");
      expect(jsonBody["signature-positionType"]).to.equal("Variable");
      expect(jsonBody["signature-offset"]).to.equal("0");
      expect(jsonBody["signature-maxOffset"]).to.equal("0");
      expect(jsonBody["signature-byteSequence"]).to.equal("ABCDE");
      expect(jsonBody["signature-endianness"]).to.equal("Little-endian");
      expect(jsonBody["signature-name"]).to.equal("Signature name");
      expect(jsonBody["signature-note"]).to.equal("Signature note");
      expect(response.statusCode).to.equal(302);
      expect(response.headers["location"]).to.equal("/submissions-received/1");
    });
  });

  it("should render the submission received page", () => {
    cy.get("form[action='/submissions']").submit();
    cy.get(
      "a[href='https://github.com/nationalarchives/pronom-signatures/pull/1']",
    ).should("exist");
  });
});
