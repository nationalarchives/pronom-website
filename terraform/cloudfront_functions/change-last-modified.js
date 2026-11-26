/* eslint-disable */
function handler(event) {
    const response = event.response
    response.headers["last-modified"] = {value: "${last_modified_header_value}"}
    return response;
}