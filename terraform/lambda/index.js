/* eslint-disable */
function handler(event) {
  const request = event.request;
  if (!request.uri.includes("/signatures/")) {
    request.uri = request.uri.toLowerCase();
  }
  return request;
}
/* eslint-enable */
