import React, { Component } from 'react';
import { debounce } from 'lodash';

import './App.css';

import api from './api'
import Search from './components/Search'
import Locations from './components/Locations'

class App extends Component {
  constructor(props) {
    super(props)
    this.handleChange = this.handleChange.bind(this)
    this.handleFetch = this.handleFetch.bind(this)
  }

  state = {
    query: 'default text',
    locations: []
  }

  handleSearch(locations) {
    this.setState({ locations: locations })
  }

  handleFetch = debounce(
    async function (q) {
      const res = await fetch(api.location())
      const data = await res.json()
      this.setState({ locations: data.results })
    }
    , 300
  )

  handleSubmit(e) {
    // TODO: implement
    e.preventDefault()
  }

  handleChange(e) {
    this.setState(
      { query: e.target.value },
      () => this.handleFetch(this.state.query)
    )
  }

  render() {
    return (
      <div className="App">
        <Search
          query={this.state.query}
          handleSubmit={this.handleSubmit}
          handleChange={this.handleChange}
        />
        <Locations locations={this.state.locations} />
      </div>
    );
  }
}

export default App;
