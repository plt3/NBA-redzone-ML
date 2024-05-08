(function () {
  // mute/unmute all video elements on page
  Array.from(document.querySelectorAll("video")).forEach(
    (e) => (e.muted = MUTE_STREAM),
  );
})();
