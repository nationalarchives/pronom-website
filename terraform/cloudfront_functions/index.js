/* eslint-disable */
function redirect(uri) {
  return {
    statusCode: 301,
    statusDescription: "Moved Permanently",
    headers: {
      location: {
        value: uri,
      },
    },
  };
}

function handler(event) {
  const request = event.request;
  const uri = request.uri
  const uriLower = uri.toLowerCase()
  if (!uri.includes("/signatures/") && uri !== uriLower) {
    return redirect(`/${uriLower.replace(/^\/+/, "")}`)
  }
  if (uriLower.includes("basicsearch")) {
    return redirect("/search")
  }
  if (uriLower.includes("default.aspx") || uriLower.includes("default.htm")) {
    return redirect("/")
  }
  return request;
}