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
  if (
      !request.uri.includes("/signatures/") &&
      request.uri !== request.uri.toLowerCase()
  ) {
    return redirect(`/${request.uri.toLowerCase().replace(/^\/+/, "")}`)
  } else if (request.uri.toLowerCase().includes("basicsearch")) {
    return redirect("/search")

  } else if (request.uri.toLowerCase().includes("default.aspx")) {
    return redirect("/")
  } else {
    return request;
  }
}