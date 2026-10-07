/* eslint-disable */
function handler(event) {
  const request = event.request;
  if (
    !request.uri.includes("/signatures/") &&
    request.uri !== request.uri.toLowerCase()
  ) {
    return {
      statusCode: 302,
      statusDescription: "Found",
      headers: {
        location: { value: request.uri.toLowerCase() },
      },
    };
  } else {
    return request;
  }
}
/* eslint-enable */
