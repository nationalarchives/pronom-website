document.addEventListener("DOMContentLoaded", function () {
  TNAFrontend.initAll()
  const form = document.querySelector('form')
  if (form) {
    if (form.method == "post") {
      form.onsubmit = _ => {
        const button = document.querySelector('button[type=submit]')
        button.disabled = true
        button.innerHTML = "Processing..."
      }
    }
  }
});
