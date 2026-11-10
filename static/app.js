(function () {
  "use strict";

  var RESISTOR_FIELDS = ["r1", "r2", "rc", "re"];

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
})();
