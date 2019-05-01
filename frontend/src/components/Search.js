import React from 'react';

const Search = ({ query, handleSubmit, handleChange, handleClear }) => (
  <form className="search" onSubmit={handleSubmit}>
    <div className="search-input-wrapper">
      <input
        className="search-input"
        placeholder="Start typing..."
        value={query}
        onChange={handleChange}
      />
      {
        query && <button
          className="button-clear"
          type="button"
          onClick={handleClear}
        ></button>
      }
    </div>
    <button className="button-submit" type="submit">⏵</button>
  </form>
);

export default Search;