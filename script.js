const DOWNLOAD_URL = "https://github.com/1moonbyte1/DSiForge";

document.querySelectorAll(".copy-button").forEach((button) => {
  button.addEventListener("click", async () => {
    const value = button.dataset.copy;
    try {
      await navigator.clipboard.writeText(value);
      button.textContent = "Copied";
      window.setTimeout(() => {
        button.textContent = "Copy";
      }, 1200);
    } catch {
      button.textContent = "Select";
    }
  });
});

document.querySelectorAll("[data-download-button]").forEach((button) => {
  if (!DOWNLOAD_URL) {
    button.setAttribute("aria-disabled", "true");
    button.addEventListener("click", (event) => {
      event.preventDefault();
      button.textContent = "GitHub link coming soon";
      window.setTimeout(() => {
        button.textContent = "Download from GitHub";
      }, 1600);
    });
    return;
  }

  button.setAttribute("href", DOWNLOAD_URL);
});
