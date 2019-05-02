import React, { Component } from "react";
import { debounce } from "lodash";
import axios from "axios";

import "./variables.css";
import "./App.css";

import api from "./api";
import Logo from "./components/Logo";
import Search from "./components/Search";
import Locations from "./components/Locations";

class App extends Component {
  constructor(props) {
    super(props);
    this.handleFetch = this.handleFetch.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.handleClear = this.handleClear.bind(this);
  }

  state = {
    query: "",
    responseQuery: "",
    locations: []
  };

  handleSearch(locations) {
    this.setState({ locations: locations });
  }

  handleFetch = debounce(async function(query) {
    const name = query.trim();
    if (name.length > 1) {
      try {
        const {
          data: { results: locations, query: responseQuery }
        } = await axios.get(api.location(), {
          params: { q: name }
        });
        this.setState({ locations, responseQuery });
      } catch (err) {
        console.error(err);
        this.setState({ locations: [], responseQuery: "" });
      }
    } else {
      this.setState({ locations: [], responseQuery: "" });
    }
  }, 100);

  handleSubmit(e) {
    e.preventDefault();
  }

  handleChange(e) {
    this.setState({ query: e.target.value }, () =>
      this.handleFetch(this.state.query)
    );
  }

  handleClear(e) {
    this.setState({ query: "", locations: [] });
  }

  render() {
    return (
      <div className="App">
        <header className="header">
          <Logo />
          <Search
            query={this.state.query}
            handleSubmit={this.handleSubmit}
            handleChange={this.handleChange}
            handleClear={this.handleClear}
          />
        </header>
        <div className="location-container">
          <Locations
            locations={this.state.locations}
            query={this.state.responseQuery}
          />
        </div>
      </div>
    );
  }
}

export default App;
