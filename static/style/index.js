let map, infoWindow;

function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 43.6532, lng: -79.3832 },
    zoom: 6,
  });
  infoWindow = new google.maps.InfoWindow();
}
