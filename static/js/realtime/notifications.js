(function () {
  const userId = document.body.dataset.userId;
  if (!userId) {
    return;
  }
  const badge = document.querySelector("[data-notifications-badge]");
  const list = document.querySelector("[data-notifications-list]");
  const toggle = document.querySelector("[data-notifications-toggle]");
  if (!list) {
    return;
  }

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop().split(";").shift();
    }
    return "";
  }

  function updateBadge(count) {
    if (!badge) {
      return;
    }
    if (!count) {
      badge.style.display = "none";
      badge.textContent = "0";
      return;
    }
    badge.textContent = String(count);
    badge.style.display = "inline-block";
  }

  function currentCount() {
    if (!badge || !badge.textContent) {
      return 0;
    }
    const parsed = parseInt(badge.textContent, 10);
    return Number.isNaN(parsed) ? 0 : parsed;
  }

  function iconFor(kind) {
    if (kind === "message") {
      return "bi-chat-dots text-primary";
    }
    if (kind === "invite") {
      return "bi-envelope-paper text-warning";
    }
    return "bi-briefcase text-success";
  }

  function prependNotification(notification) {
    const empty = list.querySelector("[data-notifications-empty]");
    if (empty) {
      empty.remove();
    }
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.className = "dropdown-item d-flex align-items-start gap-2";
    link.href = notification.link;
    const icon = document.createElement("i");
    icon.className = `bi ${iconFor(notification.kind)} mt-1`;
    const content = document.createElement("div");
    const title = document.createElement("div");
    title.className = "fw-semibold";
    title.textContent = notification.title;
    const body = document.createElement("small");
    body.className = "text-muted";
    body.textContent = notification.body || "";
    content.appendChild(title);
    content.appendChild(body);
    link.appendChild(icon);
    link.appendChild(content);
    item.appendChild(link);
    const header = list.querySelector(".dropdown-header");
    if (header && header.nextSibling) {
      list.insertBefore(item, header.nextSibling);
    } else {
      list.appendChild(item);
    }
  }

  if (toggle) {
    toggle.addEventListener("shown.bs.dropdown", function () {
      const count = currentCount();
      if (!count) {
        return;
      }
      fetch("/messages/notifications/mark-read/", {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
      }).then(function () {
        updateBadge(0);
      });
    });
  }

  const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
  const wsUrl = `${wsScheme}://${window.location.host}/ws/notifications/`;
  const socket = new WebSocket(wsUrl);

  socket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    if (data.type !== "notification") {
      return;
    }
    prependNotification(data);
    updateBadge(currentCount() + 1);
  };
})();
