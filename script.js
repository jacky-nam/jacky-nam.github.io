(function () {
  "use strict";

  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !prefersReduced) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e, i) => {
          if (e.isIntersecting) {
            e.target.style.transitionDelay = Math.min(i * 60, 180) + "ms";
            e.target.classList.add("is-visible");
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }
    );
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("is-visible"));
  }
})();

(function () {
  "use strict";

  var forms = document.querySelectorAll("form.cform");
  if (!forms.length) return;

  var keyMeta = document.querySelector('meta[name="web3forms-key"]');
  var KEY = keyMeta ? keyMeta.content.trim() : "";

  function setStatus(el, kind, msg) {
    el.textContent = msg;
    el.className = "cform__status is-" + kind;
  }

  forms.forEach(function (form) {
    var status = form.querySelector(".cform__status");
    var btn = form.querySelector('button[type="submit"]');
    var btnLabel = btn ? btn.textContent : "Send";

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      setStatus(status, "", "");

      var hp = form.querySelector('input[name="botcheck"]');
      if (hp && hp.checked) return;

      if (!form.checkValidity()) {
        var needsMsg = !!form.querySelector("textarea");
        setStatus(status, "err",
          needsMsg ? "Please add a message and a valid email." : "Please enter a valid email so I can reply.");
        return;
      }

      if (!KEY || KEY.indexOf("YOUR_") === 0) {
        setStatus(status, "err", "Form isn't set up yet, email jackynam@outlook.com instead.");
        return;
      }

      var data = new FormData(form);
      data.append("access_key", KEY);

      btn.disabled = true;
      btn.textContent = "Sending…";

      fetch("https://api.web3forms.com/submit", {
        method: "POST",
        headers: { Accept: "application/json" },
        body: data
      })
        .then(function (r) { return r.json(); })
        .then(function (json) {
          if (json.success) {
            setStatus(status, "ok", form.getAttribute("data-success") || "Thanks, I'll be in touch.");
            form.reset();
          } else {
            setStatus(status, "err", (json.message || "Something went wrong.") + " You can email me directly instead.");
          }
        })
        .catch(function () {
          setStatus(status, "err", "Network error, please email me at jackynam@outlook.com.");
        })
        .finally(function () {
          btn.disabled = false;
          btn.textContent = btnLabel;
        });
    });
  });
})();
