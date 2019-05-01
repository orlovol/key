import React from 'react';

const Search = ({ query, handleSubmit, handleChange }) => (
  <form onSubmit={handleSubmit} onChange={handleChange}>
    <input
      defaultValue={query}
      placeholder="Start typing..." />
  </form>
);

export default Search;