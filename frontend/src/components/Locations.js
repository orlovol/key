import React from "react";
import Location from "./Location";
import "./Locations.css";

const Locations = ({ locations, query }) => (
  <ul className="locations">
    {locations.map(location => (
      <Location key={location.id} location={location} query={query} />
    ))}
  </ul>
);

export default Locations;
