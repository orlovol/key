import React from "react";

import "./Search.css";

const Search = ({ query, handleSubmit, handleChange, handleClear }) => (
  <form className="search" onSubmit={handleSubmit}>
    <div className="search-input-wrapper">
      <input
        className="search-input"
        placeholder="Починайте вводити"
        value={query}
        onChange={handleChange}
        autoFocus={true}
      />
      {query && (
        <button className="button-clear" type="button" onClick={handleClear}>
          &times;
        </button>
      )}
    </div>
  </form>
);

export default Search;
