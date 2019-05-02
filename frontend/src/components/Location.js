import React, { Fragment } from "react";
import "./Location.css";

const Type_Map = {
  region: "область",
  raion: "район",
  city: "місто",
  district: "район",
  microdistrict: "мікрорайон",
  street: "вулиця",
  address: "адреса"
};

const Location = ({ location, query }) => {
  const { names, type } = location;
  const relevantName = Array.isArray(names) ? names[0] : null;
  const [name, parent] = relevantName;

  const nameMatched = name => {
    const queryPos = name.toLowerCase().indexOf(query, 0);
    if (queryPos < 0) {
      return name;
    }
    const prefix = name.slice(0, queryPos);
    const match = name.slice(queryPos, queryPos + query.length);
    const suffix = name.slice(queryPos + query.length);
    return (
      <Fragment>
        {prefix}
        <em>{match}</em>
        {suffix}
      </Fragment>
    );
  };

  return (
    Boolean(relevantName) && (
      <li className="location">
        <div className="location__item">
          <p>{nameMatched(name)}</p>
          <p className="location__parent">{parent}</p>
        </div>
        <span className="location__type">{Type_Map[type]}</span>
      </li>
    )
  );
};

export default Location;
