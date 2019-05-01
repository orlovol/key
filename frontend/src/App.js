import React, { Component } from 'react';
import { debounce } from 'lodash';
import axios from 'axios';

import './App.css';

import api from './api'
import Search from './components/Search'
import Locations from './components/Locations'

class App extends Component {
  constructor(props) {
    super(props)
    this.handleFetch = this.handleFetch.bind(this)
    this.handleSubmit = this.handleSubmit.bind(this)
    this.handleChange = this.handleChange.bind(this)
    this.handleClear = this.handleClear.bind(this)
  }

  state = {
    query: '',
    locations: []
  }

  handleSearch(locations) {
    this.setState({ locations: locations })
  }

  handleFetch = debounce(
    async function (query) {
      try {
        const { data: { results: locations } } = await axios.get(
          api.location(),
          {
            params: { name: query.trim() }, // TODO: search only on at least two characters
          }
        )
        this.setState({ locations })
      } catch (err) {
        console.error(err)
        this.setState({ locations: [] })
      }
    }
    , 150
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

  handleClear(e) {
    this.setState(
      { query: "", locations: [] }
    )
  }

  render() {
    return (
      <div className="App">
        <div className="search-container">
          <Search
            query={this.state.query}
            handleSubmit={this.handleSubmit}
            handleChange={this.handleChange}
            handleClear={this.handleClear}
          />
        </div>
        <div className="location-container">
          <Locations locations={this.state.locations} />
        </div>
      </div>
    );
  }
}

export default App;
