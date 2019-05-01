import React, { Component } from 'react';
import { debounce } from 'lodash';

class Search extends Component {
  constructor(props) {
    super(props)
    this.handleChange = this.handleChange.bind(this)
    this.handleFetch = this.handleFetch.bind(this)
  }
  state = {
    query: 'default text'
  }
  handleSubmit(e) {
    e.preventDefault()
  }

  sendRequest = debounce(
    function (r) {
      // send request to load suggestions
      console.log("Send request: " + r)
    }
    , 300
  )

  handleFetch(query) {
    // fetch suggestions
    this.sendRequest(query)
  }
  handleChange(e) {
    this.setState({ query: e.target.value }, this.handleFetch(this.state.query))
  }
  render() {
    return (
      <form onSubmit={this.handleSubmit} onChange={this.handleChange}>
        <input
          defaultValue={this.state.query}
          placeholder="Start typing..." />
      </form>
    );
  }
}

export default Search;