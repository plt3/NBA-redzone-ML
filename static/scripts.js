const halftime_button = document.getElementById("halftime-button");
const commercial_button = document.getElementById("commercial-button");
const nba_button = document.getElementById("nba-button");
let prev_commercial_val = null;
let prev_nba_val = null;

async function make_fetch(endpoint) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
  });
  const response_obj = await response.json();
  return response_obj;
}

async function force_halftime() {
  const response_obj = await make_fetch("/force-halftime");
  halftime_button.disabled = true;
  commercial_button.disabled = true;

  if (prev_commercial_val !== null) {
    commercial_button.textContent = prev_commercial_val;
    prev_commercial_val = null;
  }

  if (prev_nba_val !== null) {
    nba_button.textContent = prev_nba_val;
    prev_nba_val = null;
  }

  // disable halftime button and commercial button until halftime is over
  if (response_obj.hasOwnProperty("timeout")) {
    setTimeout(() => {
      halftime_button.disabled = false;
      commercial_button.disabled = false;
    }, response_obj["timeout"] * 1000);
  }
}

async function force_commercial() {
  const response_obj = await make_fetch("/force-commercial");

  if (prev_commercial_val === null) {
    if (prev_nba_val !== null) {
      nba_button.textContent = prev_nba_val;
      prev_nba_val = null;
    }
    prev_commercial_val = commercial_button.textContent;
  } else if (prev_commercial_val !== null) {
    prev_commercial_val = null;
  }

  commercial_button.textContent = response_obj.next_action;
}

async function force_nba() {
  const response_obj = await make_fetch("/force-nba");

  if (prev_nba_val === null) {
    if (prev_commercial_val !== null) {
      commercial_button.textContent = prev_commercial_val;
      prev_commercial_val = null;
    }
    prev_nba_val = nba_button.textContent;
  } else if (prev_nba_val !== null) {
    prev_nba_val = null;
  }

  nba_button.textContent = response_obj.next_action;
}

window.onload = () => {
  halftime_button.onclick = async () => {
    await force_halftime();
  };
  commercial_button.onclick = async () => {
    await force_commercial(commercial_button);
  };
  nba_button.onclick = async () => {
    await force_nba(nba_button);
  };
};
