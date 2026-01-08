(function () {
  const container = document.getElementById("chatMessages");
  if (!container) {
    return;
  }
  const conversationId = container.dataset.conversationId;
  const currentUserId = container.dataset.currentUserId;
  if (!conversationId) {
    return;
  }
  const form = document.getElementById("chatForm");
  const input = document.getElementById("chatInput");

  function scrollToBottom() {
    container.scrollTop = container.scrollHeight;
  }

  function renderMessage(message) {
    const wrapper = document.createElement("div");
    const isOutgoing = String(message.sender_id) === String(currentUserId);
    const classes = ["chat-message"];
    classes.push(isOutgoing ? "chat-message--outgoing" : "chat-message--incoming");
    if (message.kind === "system") {
      classes.push("chat-message--system");
    }
    wrapper.className = classes.join(" ");
    const bubble = document.createElement("div");
    bubble.className = "chat-message__bubble";
    const body = document.createElement("div");
    body.className = "chat-message__body";
    body.textContent = message.body;
    const meta = document.createElement("div");
    meta.className = "chat-message__meta";
    const sender = document.createElement("span");
    sender.textContent = message.sender_name;
    const time = document.createElement("span");
    time.textContent = new Date(message.created_at).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    meta.appendChild(sender);
    meta.appendChild(time);
    bubble.appendChild(body);
    bubble.appendChild(meta);
    wrapper.appendChild(bubble);
    container.appendChild(wrapper);
    scrollToBottom();
  }

  const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
  const wsUrl = `${wsScheme}://${window.location.host}/ws/messages/${conversationId}/`;
  const socket = new WebSocket(wsUrl);

  socket.onopen = function () {
    socket.send(JSON.stringify({ type: "read" }));
    scrollToBottom();
  };

  socket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    if (data.type !== "message") {
      return;
    }
    renderMessage(data);
  };

  if (form && input) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      const body = input.value.trim();
      if (!body) {
        return;
      }
      socket.send(JSON.stringify({ type: "message", body: body }));
      input.value = "";
    });
  }

  scrollToBottom();
})();
