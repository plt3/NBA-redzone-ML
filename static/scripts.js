window.onload = () => {
  const halftime_button = document.getElementById("halftime-button");

  halftime_button.onclick = async () => {
    // start/pause/resume halftime with halftime-button
    const response = await fetch("/halftime", { method: "POST" });
    const response_obj = await response.json();
    halftime_button.textContent = response_obj.next_action;

    // disable button after halftime ends
    if (response_obj.hasOwnProperty("timeout")) {
      setTimeout(() => {
        halftime_button.textContent = "Start halftime";
      }, response_obj["timeout"] * 1000);
    }
  };
};
