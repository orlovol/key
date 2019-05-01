import React from 'react';
import Location from './Location'

const Locations = ({ locations }) => (
  <ul>
    {
      locations.map(location =>
        <Location key={location.id} location={location} />
      )
    }
  </ul>
);

export default Locations;