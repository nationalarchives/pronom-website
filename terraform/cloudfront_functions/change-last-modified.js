/* eslint-disable */
function handler(event) {
    const request = event.request
    const response = event.response
    if (request.uri.toLowerCase().includes("container-signature.xml")) {
        response.headers["last-modified"] = {value: "Tue, 27 Oct 2026 11:19:09 GMT"}
    }
    return response;
}