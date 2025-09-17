import { CyHttpMessages } from "cypress/types/net-stubbing";
import IncomingRequest = CyHttpMessages.IncomingRequest;
import Chainable = Cypress.Chainable;

const getElement: (label: string) => Chainable<JQuery> = (label) =>
  cy.contains(label).first().parent().parent().next();

const checkInput: (label: string, className: string) => void = (
  label,
  className,
) => getElement(label).should("have.class", className);

const checkSelectInput: (label: string, expectedValue: string) => void = (
  label,
  expectedValue,
) => {
  checkInput(label, "tna-select");
  cy.contains(label)
    .parent()
    .parent()
    .next()
    .should("have.value", expectedValue);
};
const checkTextInput: (label: string) => void = (label) =>
  checkInput(label, "tna-text-input");

const checkTextValue: (label: string, value: string) => void = (
  label,
  value,
) => {
  checkTextInput(label);
  getElement(label).should("have.value", value);
};

const jsonFromForm: (request: IncomingRequest) => { [p: string]: string } = (
  request,
) => {
  const params: URLSearchParams = new URLSearchParams(request.body);
  return Object.fromEntries(params.entries());
};
export { checkTextInput, checkSelectInput, checkTextValue, jsonFromForm };
