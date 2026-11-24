(function () {
  "use strict";

  var RESISTOR_FIELDS = ["r1", "r2", "rb", "rc", "re"];

  function unitLabel() {
    var select = document.getElementById("unit");
    return select && select.value === "ohm" ? "Ω" : "kΩ";
  }

  function valueOf(id) {
    var input = document.getElementById(id);
    if (!input) {
      return "—";
    }
    var value = input.value.trim();
    return value === "" ? "—" : value;
  }

  function refresh() {
    var unit = unitLabel();

    var vcc = document.getElementById("c-vcc");
    if (vcc) {
      vcc.textContent = valueOf("vcc") + " V";
    }

    var beta = document.getElementById("c-beta");
    if (beta) {
      beta.textContent = "β = " + valueOf("beta");
    }

    RESISTOR_FIELDS.forEach(function (field) {
      var label = document.getElementById("c-" + field);
      if (label) {
        label.textContent =
          field.toUpperCase() + " = " + valueOf(field) + " " + unit;
      }
    });
  }

  document.addEventListener("input", refresh);
  document.addEventListener("change", refresh);
  refresh();

  function setupSimulationPending() {
    var form = document.querySelector(".sim-form");
    var button = form && form.querySelector(".sim-run");
    var results = document.querySelector(".sim-results");
    var status = document.getElementById("sim-status");
    if (!form || !button || !results) {
      return;
    }

    var originalLabel = button.textContent;
    var originalStatusChildren = status
      ? Array.from(status.childNodes, function (node) {
          return node.cloneNode(true);
        })
      : null;

    form.addEventListener("submit", function () {
      button.disabled = true;
      button.textContent = "Running ngspice…";
      results.dataset.pending = "true";
      results.setAttribute("aria-busy", "true");
      if (status) {
        status.dataset.state = "pending";
        status.textContent = "Running ngspice…";
      }
      try {
        sessionStorage.setItem("ce-sim-pending", "1");
      } catch (error) {
        /* Storage can be disabled; pending UI still works in this document. */
      }
    });

    function reset() {
      button.disabled = false;
      button.textContent = originalLabel;
      results.dataset.pending = "false";
      results.setAttribute("aria-busy", "false");

      var wasPending = false;
      try {
        wasPending = sessionStorage.getItem("ce-sim-pending") === "1";
        sessionStorage.removeItem("ce-sim-pending");
      } catch (error) {
        /* Ignore disabled storage. */
      }

      if (status && originalStatusChildren) {
        status.replaceChildren.apply(
          status,
          originalStatusChildren.map(function (node) {
            return node.cloneNode(true);
          })
        );
        status.dataset.state = results.getAttribute("data-sim-state") || "idle";
      }
      if (wasPending) {
        var heading = document.getElementById("sim-results-heading");
        if (heading) {
          heading.focus();
        }
      }
    }

    window.addEventListener("pageshow", reset);
  }

  setupSimulationPending();
})();
