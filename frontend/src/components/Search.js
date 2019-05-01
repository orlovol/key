import React from "react";

import "./Search.css";

const Search = ({ query, handleSubmit, handleChange, handleClear }) => (
  <form className="search" onSubmit={handleSubmit}>
    <div className="search-input-wrapper">
      {query && (
        <button className="button-clear" type="button" onClick={handleClear}>
          &times;
        </button>
      )}
      <input
        className="search-input"
        placeholder="Start typing..."
        value={query}
        onChange={handleChange}
      />
      {query && (
        <button className="button-submit" type="submit">
          ▶
        </button>
      )}
    </div>
  </form>
);

export default Search;
