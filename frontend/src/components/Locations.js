import React from 'react';
import Location from './Location'
import './Locations.css'

const Locations = ({ locations }) => (
  <ul className="locations">
    {
      locations.map(location =>
        <Location key={location.id} location={location} />
      )
    }
  </ul>
);

export default Locations;