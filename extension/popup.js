document.getElementById("open-gmaps").addEventListener("click", () => {
  chrome.tabs.create({ url: "https://www.google.com/maps" });
});
