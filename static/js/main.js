document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector(".site-nav");
  toggle?.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
    toggle.querySelector("i").className = `bi bi-${open ? "x" : "list"}`;
  });

  document.querySelectorAll(".toast button").forEach((button) =>
    button.addEventListener("click", () => button.parentElement.remove()),
  );
  setTimeout(() => document.querySelectorAll(".toast").forEach((toast) => toast.remove()), 6000);

  document.querySelectorAll("form[data-confirm]").forEach((form) =>
    form.addEventListener("submit", (event) => {
      if (!confirm(form.dataset.confirm)) event.preventDefault();
    }),
  );

  document.querySelectorAll("[data-copy]").forEach((button) =>
    button.addEventListener("click", async () => {
      await navigator.clipboard.writeText(button.dataset.copy);
      button.innerHTML = '<i class="bi bi-check2"></i>';
      button.setAttribute("aria-label", "Link copied");
    }),
  );

  document.querySelectorAll("[data-count-for]").forEach((output) => {
    const input = document.getElementById(output.dataset.countFor);
    const update = () => (output.textContent = `${input.value.length} characters`);
    input.addEventListener("input", update);
    update();
  });

  // A URL and a local file represent two mutually exclusive image sources.
  document.querySelectorAll("[data-image-url]").forEach((urlInput) => {
    const fileInput = document.getElementById(urlInput.dataset.imageUrl);
    if (!fileInput) return;
    const sync = () => {
      const hasUrl = urlInput.value.trim().length > 0;
      const hasFile = fileInput.files.length > 0;
      fileInput.disabled = hasUrl;
      urlInput.disabled = hasFile;
      urlInput.closest(".field")?.classList.toggle("field-disabled", hasFile);
      fileInput.closest(".field")?.classList.toggle("field-disabled", hasUrl);
    };
    urlInput.addEventListener("input", sync);
    fileInput.addEventListener("change", sync);
    sync();
  });
});
