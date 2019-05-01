import React from 'react';

const Location = ({ location }) => (
  <li className="location">
    {location.id} - {location.name} - {location.type}
  </li>
);

export default Location;