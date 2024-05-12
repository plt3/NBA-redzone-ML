const DEFAULT_BREAK_DURATION = 30;

// TODO: update API routes/calls

async function timed_break(element, halftime = true, duration = 0) {
  const response = await fetch("/timed-break", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ halftime: halftime, duration: duration }),
  });
  const response_obj = await response.json();
  element.disabled = true;

  if (response_obj.hasOwnProperty("timeout")) {
    setTimeout(() => {
      element.disabled = false;
    }, response_obj["timeout"] * 1000);
  }
}

async function untimed_break() {
  const response = await fetch("/untimed-break", { method: "POST" });
  await response.json();
}

window.onload = () => {
  const halftime_button = document.getElementById("halftime-button");
  const timed_break_button = document.getElementById("timed-break-button");
  timed_break_button.textContent = `Start ${DEFAULT_BREAK_DURATION} second break`;
  const untimed_break_button = document.getElementById("untimed-break-button");

  halftime_button.onclick = async () => {
    await timed_break(halftime_button, true, null);
  };
  timed_break_button.onclick = async () => {
    await timed_break(timed_break_button, false, DEFAULT_BREAK_DURATION);
  };
  untimed_break_button.onclick = async () => {
    await untimed_break();
  };
};
