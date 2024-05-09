window.onload = () => {
  document.getElementById("halftime-button").onclick = async () => {
    const response = await fetch("/halftime");
    // const scoresArr = await response.json();
  };
};
