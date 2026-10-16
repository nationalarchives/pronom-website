/* eslint-disable */
function handler(event) {
  const request = event.request;
  if (
    !request.uri.includes("/signatures/") &&
    request.uri !== request.uri.toLowerCase()
  ) {
    return {
      statusCode: 301,
      statusDescription: "Moved Permanently",
      headers: {
        location: {
          value: `/${request.uri.toLowerCase().replace(/^\/+/, "")}`,
        },
      },
    };
  } else {
    return request;
  }
}
/* eslint-enable */
