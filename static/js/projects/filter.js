document.addEventListener("DOMContentLoaded", function () {
  const typeSelect = document.getElementById("typeSelect");
  const budgetSelect = document.getElementById("budgetSelect");
  const sortSelect = document.getElementById("sortSelect");
  const filtersForm = document.getElementById("filtersForm");

  if (!typeSelect || !budgetSelect) return;

  function syncBudgetState() {
    const isHourly = typeSelect.value === "hourly";
    budgetSelect.disabled = isHourly;

    if (isHourly) {
      budgetSelect.value = "";
    }
  }

  typeSelect.addEventListener("change", syncBudgetState);
  syncBudgetState(); // ?????? ???????????'??????????-

  if (sortSelect && filtersForm) {
    sortSelect.addEventListener("change", function () {
      filtersForm.submit();
    });
  }
});
