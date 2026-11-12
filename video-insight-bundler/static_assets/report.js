(function () {
  function renderTranscript() {
    var dataNode = document.getElementById("transcriptData");
    var list = document.getElementById("transcriptList");
    if (!dataNode || !list) return;
    var rows = [];
    try { rows = JSON.parse(dataNode.textContent || "[]"); } catch (error) { rows = []; }
    var search = document.getElementById("transcriptSearch");
    var tone = document.getElementById("toneFilter");
    function esc(value) {
      return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) {
        return {"&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"}[char];
      });
    }
    function highlight(text, query) {
      var safe = esc(text);
      if (!query) return safe;
      var pattern = new RegExp("(" + query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
      return safe.replace(pattern, "<mark>$1</mark>");
    }
    function paint() {
      var q = (search && search.value || "").trim().toLowerCase();
      var toneValue = tone && tone.value || "";
      var filtered = rows.filter(function (row) {
        return (!q || String(row.text || "").toLowerCase().indexOf(q) >= 0) && (!toneValue || row.tone === toneValue);
      });
      list.innerHTML = filtered.map(function (row) {
        var markers = (row.markers || []).join(", ") || "none";
        return "<article class='transcript-item' data-tone='" + esc(row.tone) + "'>" +
          "<div class='meta'>" + esc(row.start) + "s-" + esc(row.end) + "s | tone: " + esc(row.tone) + " | WPM: " + esc(row.wpm) + " | markers: " + esc(markers) + "</div>" +
          "<div>" + highlight(row.text || "", q) + "</div>" +
          "</article>";
      }).join("") || "<p>No transcript rows match the current filter.</p>";
    }
    if (search) search.addEventListener("input", paint);
    if (tone) tone.addEventListener("change", paint);
    paint();
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderTranscript);
  } else {
    renderTranscript();
  }
}());
