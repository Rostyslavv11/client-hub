(function () {
  const linkWrap = document.querySelector(".portfolio-link-field");
  const fileWrap = document.querySelector(".portfolio-file-field");
  const linkInput = linkWrap ? linkWrap.querySelector("input") : null;
  const fileInput = fileWrap ? fileWrap.querySelector("input") : null;
  const linkRadio = document.getElementById("portfolio_method_link");
  const fileRadio = document.getElementById("portfolio_method_file");

  if (!linkWrap || !fileWrap || !linkInput || !fileInput || !linkRadio || !fileRadio) {
    return;
  }

  const hideClass = "portfolio-field-hidden";
  const fadeClass = "portfolio-field-fade";

  linkWrap.classList.add(fadeClass);
  fileWrap.classList.add(fadeClass);

  function clearFile() {
    fileInput.value = "";
  }

  function clearLink() {
    linkInput.value = "";
  }

  function applyState() {
    if (linkRadio.checked) {
      fileWrap.classList.add(hideClass);
      linkWrap.classList.remove(hideClass);
      clearFile();
      return;
    }

    linkWrap.classList.add(hideClass);
    fileWrap.classList.remove(hideClass);
    clearLink();
  }

  linkRadio.addEventListener("change", applyState);
  fileRadio.addEventListener("change", applyState);

  applyState();
})();
