makeMap(data.features);

// create the map
function makeMap(features){

  // define function to run on each feature
  function onEachFeature(feature, layer) {
  
    layer.bindTooltip("<h3>" + feature.properties.SERVCITY + ", " + feature.properties.STATE +
      "</h3>" + "<p>Name: " + feature.properties.NAME + "</p>" + "<p>IATA: " + feature.properties.IDENT + "</p>" 
    );
  }
  
  var token = "pk.eyJ1IjoiZGNjb21icyIsImEiOiJja2lydWVwbnkwYWg4MzVvMXJmaDhieGxrIn0.LRVQLFWbFhAjvhfCUBwjAA"
  // create dark map
  var darkmap = L.tileLayer("https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}", {
    attribution: "© <a href='https://www.mapbox.com/about/maps/'>Mapbox</a> © <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a> <strong><a href='https://www.mapbox.com/map-feedback/' target='_blank'>Improve this map</a></strong>",
    tileSize: 512,
    minZoom: 3,
    maxZoom: 12,
    zoomOffset: -1,
    id: "mapbox/dark-v10",
    accessToken: 
  });

  // create light map
  var lightmap = L.tileLayer("https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}", {
    attribution: "© <a href='https://www.mapbox.com/about/maps/'>Mapbox</a> © <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a> <strong><a href='https://www.mapbox.com/map-feedback/' target='_blank'>Improve this map</a></strong>",
    tileSize: 512,
    minZoom: 3,
    maxZoom: 12,
    zoomOffset: -1,
    id: "mapbox/light-v10",
    accessToken: token
  });

  // find the maximum number of passengers to adjust the color scale
  var maxPass = Math.max.apply(Math, features.map(function(o) { return o.properties.passengers; }))
  var minPass = Math.min.apply(Math, features.map(function(o) { return o.properties.passengers; }))
  // take the next highest integer as a scale value
  var scale = Math.ceil(maxPass-minPass)

  // create airport markers
  var topports = L.geoJSON(features, {
    onEachFeature: onEachFeature,
    pointToLayer: function (feature, coordinates) {
        return L.circleMarker(coordinates, {
          radius:20*feature.properties.passengers/scale,
          fillColor:d3.interpolateCool(0.5),
          weight:1,
          color:"white",
          fillOpacity:0.7
        });
      } 
  })

  var ports = L.geoJSON(data2.features, {
    onEachFeature: onEachFeature,
    pointToLayer: function (feature, coordinates) {
        return L.circleMarker(coordinates, {
          radius:5,
          weight:1,
          color:"white",
          fillOpacity:0.7
        });
      }
  })

  // create base layers
  var baseMaps = {
    Light: lightmap,
    Dark: darkmap
  };

  // create map object and set defaults
  var myMap = L.map("map", {
    center: [45.52, -122.67],
    zoom: 4,
    layers: [darkmap, ports]
  });



    // create feature layers    
    var featureLayers = {
      "Top 20 Airports":topports,
      "All Airports":ports
    };
    // Pass our map layers into our layer control
    // Add the layer control to the map
  L.control.layers(baseMaps,featureLayers).addTo(myMap);

}
