import { MapContainer, Marker, Popup, TileLayer, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import React, { useEffect, useState } from "react";
import { Rectangle, Polyline } from "react-leaflet";
import L from 'leaflet'

const airplanIcon = (heading)=>L.divIcon({
  html: `<div style="transform:rotate(${heading}deg); font-size:20px; color:gold;">✈</div>`,
  className: '',
  iconSize: [20, 20],
  iconAnchor: [10, 10]
})
const markerIcon = L.divIcon({
  html: `<div style="font-size:20px;">📍</div>`,
  className: '',
  iconSize: [20, 20],
  iconAnchor: [10, 10]
})
function LocationMarker({ position, setPosition }) {

  const map = useMapEvents({
    click(e) {
      setPosition(e.latlng)
    },

  })


  return position === null ? null : (
    <Marker position={position} icon={markerIcon}>
      <Popup>Latitude : {position.lat.toFixed(5)} , Longitude : {position.lng.toFixed(5)}</Popup>
    </Marker>

  )
}
function FlightData({ flights }) {

  return (<div>
    <h2>Flights</h2>
    <ul>
      {flights.map((flight, index) => (
        <li key={index}>
          ICAO24: {flight.icao24} | Callsign: {flight.callsign} | Lat: {flight.lat} | Lon: {flight.lng}
        </li>
      ))}
    </ul>
  </div>)
}
function FlightMarkers({ flights }) {
  flights = flights.filter(f => f.lng !== null && f.lat !== null)
  if (!flights || flights.length === 0) return null
  return (<>
    {flights.map((flight) => (<React.Fragment key={flight.icao24}>
      <Marker position={[flight.lat, flight.lng]} icon={airplanIcon(flight.heading)} >
        <Popup>
          Callsign: {flight.callsign}<br />
          From: {flight.route?.src_airport}, {flight.route?.src_country}<br />
          To: {flight.route?.dst_airport}, {flight.route?.dst_country}<br />
          Altitude: {flight.altitude}m | Speed: {flight.velocity}m/s
        </Popup>
      </Marker>
      {flight.route && <Polyline
        positions={[
          [Number(flight.route?.src_lat), Number(flight.route?.src_lng)],
          [flight?.lat, flight?.lng]
        ]}
        pathOptions={{ color: 'gold', weight: 2 }}
      />}
    </React.Fragment>
    ))}

  </>)
}
export default function FlightTracker() {
  const [position, setPosition] = useState(null)
  const [flights, setFlight] = useState([])
  const rectangle = position !== null ? [
    [position.lat - 1, position.lng - 1],
    [position.lat + 1, position.lng + 1]
  ] : null
  const purple = { color: 'purple' }
  useEffect(() => {
    if (!position) return
    const fetchFlights = () => {
      fetch(`https://golden-flight-tracker.onrender.com/flights?lat=${position.lat}&lng=${position.lng}`)
      .then((response) => response.json())
      .then((data) => {
        console.log(data)
        setFlight(data || {})
      })
      .catch((error) => console.error("Error:", error))
    }
    fetchFlights() // immediate first fetch
    const interval = setInterval(fetchFlights, 15000)

    return () => clearInterval(interval)
  }, [position])

  return (
    
      <MapContainer center={[51.505, -0.09]} zoom={13} style={{ height: "100vh", width: "100%", cursor: "pointer" }}>
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        />
        <LocationMarker setPosition={setPosition} position={position} />
        
        <FlightMarkers flights={flights} />

      </MapContainer>
      
    
  );
}
