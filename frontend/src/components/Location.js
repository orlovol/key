import React from 'react';
import './Location.css'

const Location = ({ location }) => (
  <li className="location">
    <p><em>{location.name}</em></p>
    <p><span>{location.type}</span></p>
  </li>
);

export default Location;