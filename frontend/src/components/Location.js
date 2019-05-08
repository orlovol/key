import React from "react";
import Highlighter from "react-highlight-words";

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
    return (
      <Highlighter
        searchWords={query.split(' ')}
        highlightTag={'em'}
        textToHighlight={name}
      />
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
