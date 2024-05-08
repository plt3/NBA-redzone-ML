(function () {
  // make object indicating if page contains an HTML video element, and with a list
  // of iframe srcs if not
  const video_obj = { iframes: [] };
  video_obj.has_video = document.querySelectorAll("video").length > 0;
  if (!video_obj.has_video) {
    video_obj.iframes = Array.from(document.querySelectorAll("iframe")).map(
      (e) => e.src,
    );
  }
  return JSON.stringify(video_obj);
})();
